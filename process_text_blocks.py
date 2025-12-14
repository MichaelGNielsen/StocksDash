import os

def process_text_blocks(input_file, output_file, separator="\t"):
    """
    Læser en tekstfil med blokke adskilt af to linjeskift, samler hver bloks linjer
    til én linje med en separator, og skriver resultatet til en ny fil.
    
    Args:
        input_file (str): Sti til input tekstfilen.
        output_file (str): Sti til output tekstfilen.
        separator (str): Separator mellem felter i output (default: tabulator).
    """
    try:
        # Læs inputfilen
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Opdel i blokke baseret på to linjeskift
        blocks = content.split('\n\n')
        processed_lines = []
        
        for block in blocks:
            # Fjern tomme linjer og strip whitespace fra hver linje
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            if lines:
                # Saml linjerne til én linje med separator
                processed_line = separator.join(lines)
                processed_lines.append(processed_line)
        
        # Skriv til outputfilen
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(processed_lines))
        
        print(f"Behandlingen er færdig! Output gemt i: {output_file}")
        print(f"Antal behandlede blokke: {len(processed_lines)}")
    
    except FileNotFoundError:
        print(f"Fejl: Inputfilen '{input_file}' blev ikke fundet.")
    except Exception as e:
        print(f"Fejl under behandlingen: {e}")

if __name__ == "__main__":
    # Definér input- og outputfil
    input_file = "input.txt"
    output_file = "output.txt"
    
    # Kør behandlingen med tabulator som separator
    process_text_blocks(input_file, output_file, separator="\t")