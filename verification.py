"""Bloc 3, couche de vérification : grandeurs attendues depuis les seules primitives.

Cette couche ne lit aucun fichier de vérité terrain. À l'exécution, l'agent
ne dispose que du plan : il juge son résultat sans référence extérieure. Le
corpus de vérité ne sert qu'aux runs d'évaluation du bloc 5, où deux solides
mesurés sont comparés l'un à l'autre.

Contrainte 1 appliquée ici : aucune grandeur dérivée lue sur le plan n'est
utilisée. Les champs bbox_x_mm, bbox_y_mm et bbox_z_mm du JSON d'extraction
sont délibérément ignorés, ce sont des valeurs lues donc invérifiables. Les
deux seules erreurs du spike portaient exactement sur ces valeurs-là.

Limite structurelle mesurée : le champ "profil" est du texte libre.
L'aire de la section n'est donc pas calculable, ce qui rend indisponibles
la bbox en X et en Y ainsi que le volume attendu. Cause unique, deux effets.
"""
from __future__ import annotations

# Périmètre géométrique borné. Toute autre valeur est signalée plutôt
# qu'interprétée.
CORPS_SUPPORTES = {"contour_extrude", "cercle_extrude"}


def _nombre(valeur):
    """Retourne un flottant, ou None si la valeur est absente ou non numérique."""
    if isinstance(valeur, (int, float)) and not isinstance(valeur, bool):
        return float(valeur)
    return None


def _etendue_z(corps: list[dict]) -> float | None:
    """Hauteur hors tout, seule dimension portée par des champs numériques dédiés."""
    bases, sommets = [], []
    for c in corps:
        base = _nombre(c.get("z_base_mm"))
        hauteur = _nombre(c.get("hauteur_extrusion_mm"))
        if base is None or hauteur is None:
            return None
        bases.append(base)
        sommets.append(base + hauteur)
    if not bases:
        return None
    return max(sommets) - min(bases)


def attendu(primitives: dict) -> dict:
    """Calcule les grandeurs dérivées à partir des seules primitives extraites.

    Les grandeurs non calculables valent None et sont nommées dans
    "non_calculable". Un None est une absence déclarée, jamais une valeur
    par défaut : une couche de vérification qui comble un trou ne vérifie plus.
    """
    corps = primitives.get("corps") or []
    trous = primitives.get("trous") or []
    poches = primitives.get("poches") or []

    hors_perimetre = [
        f"corps {c.get('nom', '?')!r} de type {c.get('type', '?')!r}"
        for c in corps
        if c.get("type") not in CORPS_SUPPORTES
    ]

    bbox_z = _etendue_z(corps)
    non_calculable = [
        "bbox_x_mm et bbox_y_mm : le champ profil est du texte libre, "
        "l'aire de la section n'est pas dérivable",
        "volume_mm3 : dépend de l'aire de la section, même cause",
    ]
    if bbox_z is None:
        non_calculable.append(
            "bbox_z_mm : z_base_mm ou hauteur_extrusion_mm absent sur au moins un corps"
        )

    return {
        # Convention de comptage alignée sur les fichiers _verite.md, pas sur
        # verify.py du spike qui comptait les borgnes comme des trous. Le prompt
        # d'extraction définit trous comme les traversants uniquement, et poches
        # comme tout enlèvement non traversant : la sémantique est portée par le
        # prompt, le code se contente de compter.
        "nb_trous_traversants": len(trous),
        "nb_poches": len(poches),
        "bbox_mm": (None, None, bbox_z),
        "volume_mm3": None,
        "non_calculable": non_calculable,
        "hors_perimetre": hors_perimetre,
    }