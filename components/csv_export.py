import csv

def export_csv(rows):
    with open(
        "cartas.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "Nome",
            "Raridade",
            "Código",
            "Variante",
            "Min",
            "Médio",
            "Max",
            "Estado"
            "Favorito"
        ])

        writer.writerows(rows)
