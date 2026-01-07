from rdkit import Chem
from rdkit.Chem import AllChem
from ase.io import read, write


mol = Chem.MolFromSmiles('C(F)(F)(F)OC(F)(F)C(F)(F)C(F)(F)OC(F)(F)C([H])([H])OC([H])([H])C([H])(C([H])([H])O)O')  # dodecane
mol = Chem.AddHs(mol)
AllChem.EmbedMolecule(mol, AllChem.ETKDG())
Chem.MolToMolFile(mol, 'd4oh.mol')
ase_mol = read('d4oh.mol')
ase_mol.write('d4oh.pdb')
