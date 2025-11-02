#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script for Paraguay Electronic Invoicing modules
"""

import os
import sys
import subprocess
from pathlib import Path


def check_odoo_version():
    """Check if Odoo is available"""
    try:
        import odoo
        print(f"✓ Odoo version {odoo.release.version} detected")
        return True
    except ImportError:
        print("✗ Odoo not found. Please install Odoo first.")
        return False


def check_dependencies():
    """Check Python dependencies"""
    required_packages = ['qrcode', 'requests', 'cryptography']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} available")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} missing")

    if missing_packages:
        print(f"\nInstalling missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', *missing_packages
            ])
            print("✓ Dependencies installed successfully")
        except subprocess.CalledProcessError:
            print("✗ Failed to install dependencies")
            return False

    return True


def setup_modules():
    """Setup the modules in Odoo addons path"""
    current_dir = Path(__file__).parent

    # Find Odoo addons path
    odoo_addons_paths = [
        Path.home() / 'odoo' / 'addons',
        Path('/opt/odoo/addons'),
        Path('/usr/lib/python3/dist-packages/odoo/addons'),
    ]

    addons_path = None
    for path in odoo_addons_paths:
        if path.exists():
            addons_path = path
            break

    if not addons_path:
        print("Could not find Odoo addons path. Please specify manually.")
        addons_path = Path(input("Enter Odoo addons path: "))

    # Create symlinks or copy modules
    modules = ['l10n_py_edi_base', 'l10n_py_edi_facturasend', 'l10n_py_edi_factpy']

    for module in modules:
        src = current_dir / module
        dst = addons_path / module

        if src.exists():
            if dst.exists():
                print(f"Module {module} already exists in addons path")
            else:
                try:
                    os.symlink(str(src), str(dst))
                    print(f"✓ Created symlink for {module}")
                except OSError:
                    # Fallback to copy
                    import shutil
                    shutil.copytree(str(src), str(dst))
                    print(f"✓ Copied {module} to addons path")
        else:
            print(f"✗ Module {module} not found")


def main():
    """Main setup function"""
    print("Paraguay Electronic Invoicing Setup")
    print("=" * 40)

    if not check_odoo_version():
        sys.exit(1)

    if not check_dependencies():
        sys.exit(1)

    print("\nSetting up modules...")
    setup_modules()

    print("\nSetup completed!")
    print("\nNext steps:")
    print("1. Restart your Odoo server")
    print("2. Go to Apps and install:")
    print("   - Paraguay - Electronic Invoicing Base")
    print("   - Paraguay - FacturaSend EDI Connector (or FactPy)")
    print("3. Configure your company and EDI provider settings")


if __name__ == '__main__':
    main()
