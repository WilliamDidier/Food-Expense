import csv
import json
import os
from datetime import datetime
from collections import defaultdict

class FoodExpenseClassifier:
    def __init__(self):
        self.config_file = "vendeurs_nourriture.json"
        self.history_file = "historique_depenses.json"
        self.load_config()
        self.load_history()
    
    def load_config(self):
        """Charge la configuration des vendeurs connus"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.food_vendors = set(data.get('nourriture', []))
                self.non_food_vendors = set(data.get('non_nourriture', []))
        else:
            self.food_vendors = set()
            self.non_food_vendors = set()
    
    def save_config(self):
        """Sauvegarde la configuration des vendeurs"""
        data = {
            'nourriture': sorted(list(self.food_vendors)),
            'non_nourriture': sorted(list(self.non_food_vendors))
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_history(self):
        """Charge l'historique des dépenses"""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
        else:
            self.history = {}
    
    def save_history(self, month, total):
        """Sauvegarde le total d'un mois dans l'historique"""
        self.history[month] = total
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def extract_vendor(self, libelle):
        """Extrait le nom du vendeur du libellé"""
        if 'Transaction carte :' in libelle:
            vendor = libelle.split('Transaction carte :')[1].strip()
            # Nettoie les numéros de transaction à la fin
            vendor = vendor.split('-')[0].strip()
            return vendor
        return None
    
    def is_food_vendor(self, vendor):
        """Vérifie si un vendeur est connu"""
        if vendor in self.food_vendors:
            return True
        if vendor in self.non_food_vendors:
            return False
        return None
    
    def classify_vendor(self, vendor):
        """Demande à l'utilisateur de classifier un vendeur"""
        print(f"\nVendeur inconnu : {vendor}")
        while True:
            response = input("Est-ce de la nourriture ? (o/n) : ").lower().strip()
            if response in ['o', 'oui', 'y', 'yes']:
                self.food_vendors.add(vendor)
                self.save_config()
                return True
            elif response in ['n', 'non', 'no']:
                self.non_food_vendors.add(vendor)
                self.save_config()
                return False
            else:
                print("Réponse invalide. Utilisez 'o' pour oui ou 'n' pour non.")
    
    def parse_date(self, date_str):
        """Parse la date au format DD/MM/YYYY"""
        return datetime.strptime(date_str, '%d/%m/%Y')
    
    def parse_amount(self, amount_str):
        """Parse le montant (remplace virgule par point)"""
        if not amount_str:
            return 0.0
        return float(amount_str.replace(',', '.'))
    
    def process_csv(self, csv_file):
        """Traite le fichier CSV et calcule les dépenses alimentaires"""
        total = 0.0
        month_key = None
        vendor_totals = defaultdict(float)

        with open(csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find header index and create reader in one go
        header_index = next((i for i, line in enumerate(lines) 
                            if 'Date' in line and 'Libellé' in line), 0)

        reader = csv.DictReader(lines[header_index:])
        for row in reader:
            libelle = row['Libellé']
            debit = row['Débit']                
            # Ignore les lignes sans débit (crédits)
            if not debit:
                continue
            
            vendor = self.extract_vendor(libelle)
            if not vendor:
                continue
            
            # Vérifie si c'est un vendeur alimentaire
            is_food = self.is_food_vendor(vendor)
            if is_food is None:
                is_food = self.classify_vendor(vendor)
            
            if not is_food:
                continue
            
            # Ajoute au total
            date = self.parse_date(row['Date'])
            if month_key is None:
                month_key = date.strftime('%Y-%m')
            amount = self.parse_amount(debit)
            total += amount
            vendor_totals[vendor] += amount

        # Sauvegarde dans l'historique
        if month_key:
            self.save_history(month_key, total)
    
        return month_key, total, vendor_totals
    
    def display_results(self, month, total, vendor_totals):
        """Affiche le total du mois et l'historique complet"""
        print("\n" + "="*50)
        print(f"DÉPENSES ALIMENTAIRES - {month}")
        print("="*50)
        print(f"Total : {total:.2f} €")
        print()

        print("PAR VENDEUR")
        print("-"*50)
        for vendor, vendor_total in sorted(vendor_totals.items(), key=lambda x: x[1]):
            print(f"{vendor:<35} {vendor_total:>10.2f} €")
        print()
        
        print("HISTORIQUE COMPLET")
        print("-"*50)
        for hist_month in sorted(self.history.keys()):
            hist_total = self.history[hist_month]
            print(f"{hist_month} : {hist_total:.2f} €")
        print("="*50)
        print()

def main():
    print("=== Classificateur de dépenses alimentaires ===\n")
    
    csv_file = input("Nom du fichier CSV à analyser : ").strip()
    
    if not os.path.exists(csv_file):
        print(f"Erreur : Le fichier '{csv_file}' n'existe pas.")
        return
    
    classifier = FoodExpenseClassifier()
    month, total, vendor_totals = classifier.process_csv(csv_file)
    classifier.display_results(month, total, vendor_totals)

if __name__ == "__main__":
    main()