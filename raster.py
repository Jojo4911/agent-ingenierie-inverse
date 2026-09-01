import sys
import fitz

chemin, grand_cote = sys.argv[1], int(sys.argv[2])
doc = fitz.open(chemin)
page = doc[0]
echelle = grand_cote / max(page.rect.width, page.rect.height)
pix = page.get_pixmap(matrix=fitz.Matrix(echelle, echelle))
sortie = chemin.replace(".pdf", f"_{pix.width}x{pix.height}.png")
pix.save(sortie)
print(sortie, pix.width, pix.height)