"""Execute public notebooks with this interpreter and a synthetic-only kernel."""
from pathlib import Path
import sys
import tempfile

import nbformat
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
from nbclient import NotebookClient


def main():
    import json
    root = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory() as directory:
        spec = Path(directory) / 'portfolio-python'
        spec.mkdir()
        (spec / 'kernel.json').write_text(json.dumps({
            'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
            'display_name': 'Portfolio Python', 'language': 'python',
        }), encoding='utf-8')
        manager = KernelSpecManager(kernel_dirs=[directory], ensure_native_kernel=False)
        for path in sorted((root / 'notebooks').glob('*.ipynb')):
            notebook = nbformat.read(path, as_version=4)
            kernel = KernelManager(kernel_name='portfolio-python', kernel_spec_manager=manager)
            NotebookClient(notebook, km=kernel, timeout=180, resources={'metadata': {'path': str(root)}}).execute()
            # Commit useful chart/table outputs, without cell execution timestamps.
            for cell in notebook.cells:
                cell.metadata.pop('execution', None)
            nbformat.write(notebook, path)
            print('Executed', path.name)


if __name__ == '__main__':
    main()
