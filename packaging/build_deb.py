import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cgp import __version__


def build(output_directory):
    output_directory = Path(output_directory).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    architecture = "all"
    package_name = f"cgp_{__version__}_{architecture}.deb"
    package_path = output_directory / package_name
    package_path.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix="cgp-deb-") as temporary_directory:
        package_root = Path(temporary_directory)
        control_directory = package_root / "DEBIAN"
        application_directory = package_root / "usr" / "lib" / "cgp"
        binary_directory = package_root / "usr" / "bin"
        desktop_directory = package_root / "usr" / "share" / "applications"
        control_directory.mkdir(parents=True)
        application_directory.mkdir(parents=True)
        binary_directory.mkdir(parents=True)
        desktop_directory.mkdir(parents=True)
        shutil.copytree(
            ROOT / "src" / "cgp",
            application_directory / "cgp",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        control = "\n".join(
            (
                "Package: cgp",
                f"Version: {__version__}",
                "Section: utils",
                "Priority: optional",
                f"Architecture: {architecture}",
                "Depends: python3 (>= 3.11), python3-tk",
                "Maintainer: CGP Contributors <beatrizcrmg@users.noreply.github.com>",
                "Homepage: https://github.com/beatrizcrmg/projeto-integrador-python",
                "Description: personal finance control application",
                " Desktop application to manage income, expenses and budgets.",
                "",
            )
        )
        (control_directory / "control").write_text(control, encoding="utf-8")
        launcher = binary_directory / "cgp"
        launcher.write_text(
            '#!/bin/sh\nPYTHONPATH="/usr/lib/cgp${PYTHONPATH:+:$PYTHONPATH}" exec /usr/bin/python3 -m cgp "$@"\n',
            encoding="utf-8",
        )
        launcher.chmod(0o755)
        desktop_entry = "\n".join(
            (
                "[Desktop Entry]",
                "Type=Application",
                "Name=CGP — Controle de Gastos Pessoais",
                "Comment=Gerencie receitas e despesas pessoais",
                "Exec=cgp",
                "Terminal=false",
                "Categories=Office;Finance;",
                "",
            )
        )
        (desktop_directory / "cgp.desktop").write_text(desktop_entry, encoding="utf-8")
        subprocess.run(
            ["dpkg-deb", "--build", "--root-owner-group", str(package_root), str(package_path)],
            check=True,
        )
    return package_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=ROOT / "dist")
    arguments = parser.parse_args()
    package_path = build(arguments.output_dir)
    print(package_path)


if __name__ == "__main__":
    main()
