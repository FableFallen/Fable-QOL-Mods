import os

def save_mod_names(mods_folder="mods", output_file="1mod_names.txt"):
    try:
        mod_files = [f for f in os.listdir(mods_folder) if f.endswith(".jar")]

        # Correct: Sort mod filenames alphabetically ignoring case
        mod_files.sort(key=lambda s: s.lower())

        with open(output_file, "w", encoding="utf-8") as file:
            for mod in mod_files:
                file.write(mod + "\n")

        print(f"Saved {len(mod_files)} mod names to {output_file}.")

    except FileNotFoundError:
        print(f"Error: The folder '{mods_folder}' does not exist. Please check your folder structure.")

if __name__ == "__main__":
    save_mod_names()
