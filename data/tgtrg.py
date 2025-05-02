import csv

def remove_column(input_file, output_file, column_name):
    with open(input_file, 'r', newline='', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        fieldnames = [field for field in reader.fieldnames if field != column_name]
        
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            del row[column_name]
            writer.writerow(row)

# Example usage
remove_column('emplo_clean_lang.csv', 'emplo_final.csv', 'seniority_level')
