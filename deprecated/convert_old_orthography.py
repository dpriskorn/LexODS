import csv

with open("ods_2021-07-30_lowercased_orthography.csv", "w") as write_file:
    with open("ods_2021-07-30.csv", "r") as file:
        # reading the CSV file
        csvFile = csv.reader(file)
        # displaying the contents of the CSV file
        for line in csvFile:
            id = line[0]
            lemma = line[1]
            category = line[2]
            if category != "Q147276":
                lemma = lemma.lower()
            if "aa" in lemma:
                lemma = lemma.replace("aa", "å")
            write_file.write(f"{id},{lemma},{category}\n")
