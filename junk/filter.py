import csv
import re

def export_filtered_gateway_configs(input_file, output_file):
    """
    Filters gateway device configurations from the input CSV file.
    Keeps rows with non-empty values in 'port_config_ge-0/0/*_*' columns (excluding '_vpn_paths_'),
    and writes the filtered data to the output CSV file.
    """
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        rows = list(reader)

    # Define base columns to always include
    base_columns = [
        "mac", "managed", "model", "name", "ntp_servers",
        "oob_ip_config_node1_type", "oob_ip_config_type", "ospf_config_enabled"
    ]

    # Identify relevant port config columns
    port_columns = [
        col for col in rows[0].keys()
        if re.match(r"(?i)port_config_ge-0/0/\d+_.*", col) and "_vpn_paths_" not in col
    ]

    columns_to_keep = base_columns + port_columns

    # Filter rows with at least one non-empty port config value
    filtered_rows = []
    for row in rows:
        if any(row.get(col) not in [None, "", "null"] for col in port_columns):
            filtered_rows.append({col: row.get(col, "") for col in columns_to_keep})

    # Write output
    if not filtered_rows:
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            f.write("No matching data found.\n")
    else:
        with open(output_file, "w", newline="", encoding="utf-8") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=columns_to_keep)
            writer.writeheader()
            writer.writerows(filtered_rows)

if __name__ == "__main__":
    input_file = "input.csv"      # Replace with your actual input file path
    output_file = "output.csv"    # Replace with your desired output file path
    export_filtered_gateway_configs(input_file, output_file)
