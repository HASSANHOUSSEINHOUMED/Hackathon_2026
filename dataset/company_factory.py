"""
Fabrique d'entreprises fictives françaises avec données réalistes.
Génère des SIRET/SIREN valides (algorithme de Luhn), des TVA intra,
des IBAN FR conformes, etc.
"""
import random
import string
from dataclasses import dataclass, field
from datetime import date

from faker import Faker

from config import BICS_FR, CODES_NAF, FORMES_JURIDIQUES

fake = Faker("fr_FR")


@dataclass
class Company:
    """Représente une entreprise fictive avec toutes ses données administratives."""
    raison_sociale: str = ""
    siren: str = ""
    siret: str = ""
    tva_intra: str = ""
    adresse_rue: str = ""
    adresse_cp: str = ""
    adresse_ville: str = ""
    iban: str = ""
    bic: str = ""
    capital_social: int = 0
    forme_juridique: str = ""
    dirigeant: str = ""
    date_creation: date = field(default_factory=date.today)
    code_naf: str = ""
    libelle_naf: str = ""


class CompanyFactory:
    """Génère des entreprises fictives avec des identifiants valides."""

    # ──────────────────────────────────────────
    # Algorithme de Luhn (validation SIREN/SIRET)
    # ──────────────────────────────────────────
    @staticmethod
    def luhn_checksum(number_str: str) -> int:
        """Calcule le checksum de Luhn pour une chaîne de chiffres."""
        digits = [int(d) for d in number_str]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        total = sum(odd_digits)
        for d in even_digits:
            total += sum(divmod(d * 2, 10))
        return total % 10

    @staticmethod
    def validate_siret(siret: str) -> bool:
        """Vérifie qu'un SIRET est valide selon l'algorithme de Luhn."""
        if len(siret) != 14 or not siret.isdigit():
            return False
        return CompanyFactory.luhn_checksum(siret) == 0

    @staticmethod
    def validate_siren(siren: str) -> bool:
        """Vérifie qu'un SIREN est valide selon l'algorithme de Luhn."""
        if len(siren) != 9 or not siren.isdigit():
            return False
        return CompanyFactory.luhn_checksum(siren) == 0

    # ──────────────────────────────────────────
    # Génération SIREN valide
    # ──────────────────────────────────────────
    @staticmethod
    def _generate_siren() -> str:
        """Génère un SIREN de 9 chiffres valide (Luhn)."""
        base = "".join([str(random.randint(0, 9)) for _ in range(8)])
        for check_digit in range(10):
            candidate = base + str(check_digit)
            if CompanyFactory.luhn_checksum(candidate) == 0:
                return candidate
        return base + "0"  # fallback, ne devrait pas arriver

    # ──────────────────────────────────────────
    # Génération SIRET valide (SIREN + NIC)
    # ──────────────────────────────────────────
    @staticmethod
    def _generate_siret(siren: str) -> str:
        """Génère un SIRET valide à partir d'un SIREN (14 chiffres, Luhn)."""
        base = siren + "".join([str(random.randint(0, 9)) for _ in range(4)])
        for check_digit in range(10):
            candidate = base + str(check_digit)
            if CompanyFactory.luhn_checksum(candidate) == 0:
                return candidate
        return base + "0"

    # ──────────────────────────────────────────
    # TVA intracommunautaire
    # ──────────────────────────────────────────
    @staticmethod
    def _compute_tva_intra(siren: str) -> str:
        """Calcule le numéro de TVA intra FR à partir du SIREN (formule officielle)."""
        siren_int = int(siren)
        cle = (12 + 3 * (siren_int % 97)) % 97
        return f"FR{cle:02d}{siren}"

    # ──────────────────────────────────────────
    # Génération IBAN FR valide (ISO 13616)
    # ──────────────────────────────────────────
    @staticmethod
    def _generate_iban_fr() -> str:
        """Génère un IBAN français valide avec checksum correct."""
        code_banque = str(random.randint(10000, 99999))
        code_guichet = str(random.randint(10000, 99999))
        numero_compte = "".join(
            random.choices(string.digits + string.ascii_uppercase, k=11)
        )
        cle_rib = str(random.randint(10, 99))

        bban = code_banque + code_guichet + numero_compte + cle_rib

        # Convertir les lettres en chiffres pour le calcul IBAN
        bban_numeric = ""
        for char in bban:
            if char.isdigit():
                bban_numeric += char
            else:
                bban_numeric += str(ord(char.upper()) - 55)

        # Ajouter FR00 converti en chiffres (F=15, R=27) -> 152700
        numeric_str = bban_numeric + "152700"
        remainder = int(numeric_str) % 97
        check_digits = 98 - remainder

        return f"FR{check_digits:02d}{bban}"

    # ──────────────────────────────────────────
    # Génération complète d'une entreprise
    # ──────────────────────────────────────────
    def generate(self) -> Company:
        """Génère une entreprise fictive complète avec identifiants valides."""
        forme = random.choice(FORMES_JURIDIQUES)
        siren = self._generate_siren()
        siret = self._generate_siret(siren)
        tva_intra = self._compute_tva_intra(siren)
        code_naf, libelle_naf = random.choice(CODES_NAF)

        company = Company(
            raison_sociale=f"{fake.company()} {forme}",
            siren=siren,
            siret=siret,
            tva_intra=tva_intra,
            adresse_rue=fake.street_address(),
            adresse_cp=fake.postcode(),
            adresse_ville=fake.city(),
            iban=self._generate_iban_fr(),
            bic=random.choice(BICS_FR),
            capital_social=random.choice(
                [1000, 5000, 10000, 50000, 100000, 200000, 500000]
            ),
            forme_juridique=forme,
            dirigeant=fake.name(),
            date_creation=fake.date_between(
                start_date=date(2000, 1, 1), end_date=date(2022, 12, 31)
            ),
            code_naf=code_naf,
            libelle_naf=libelle_naf,
        )

        return company

    def generate_batch(self, n: int) -> list[Company]:
        """Génère un lot de n entreprises fictives."""
        return [self.generate() for _ in range(n)]


if __name__ == "__main__":
    factory = CompanyFactory()
    c = factory.generate()
    print(f"Raison sociale : {c.raison_sociale}")
    print(f"SIREN : {c.siren}  (valide={factory.validate_siren(c.siren)})")
    print(f"SIRET : {c.siret}  (valide={factory.validate_siret(c.siret)})")
    print(f"TVA intra : {c.tva_intra}")
    print(f"IBAN : {c.iban}")
    print(f"BIC : {c.bic}")
    print(f"Adresse : {c.adresse_rue}, {c.adresse_cp} {c.adresse_ville}")
    print(f"Forme : {c.forme_juridique}, Capital : {c.capital_social}€")
    print(f"Dirigeant : {c.dirigeant}")
    print(f"NAF : {c.code_naf} - {c.libelle_naf}")
