from fastapi import FastAPI, Query, HTTPException
import sqlite3

app = FastAPI()

def predict_abs_t1_mod2(R_X: float, R_A: float) -> float:
    return 0.534 - 0.000327 * (R_X**9.99 + 7.99 * R_A**7.76)

def get_connection():
    return sqlite3.connect("cuprates.db")

@app.get("/")
def root():
    return {"message": "Prototype for prediction of nearest-neighbor hopping amplitude |t1| in superconducting cuprates"}

@app.get(
    "/predict_hopping_amplitude",
    summary="Predict nearest-neighbor hopping amplitude in cuprates",
    description="Uses the MOD2 equation from Moree et al., PRB 110, 014502 (2024)."
)
def predict_hopping_amplitude(
        cation_radius: float = Query(..., description="Block-layer cation radius (Angstrom)"),
        anion_radius: float = Query(..., description="Apical anion radius (Angstrom)")
):
    R_X = anion_radius
    R_A = cation_radius
    if R_X <= 0.0 or R_A <= 0.0:
        raise HTTPException(
            status_code=400,
            detail="Radii cannot be zero or negative."
        )
    t1 = predict_abs_t1_mod2(R_X, R_A)
    if t1 <= 0.0:
        raise HTTPException(
            status_code=400,
            detail="Predicted hopping amplitude is negative because the radii are too large."
        )
    
    return {
        "anion_radius_angstrom": R_X,
        "cation_radius_angstrom": R_A,
        "predicted_abs_t1_eV": t1,
        "model": "|t1| = 0.534 - 0.000327*(anion_radius_angstrom^9.99 + 7.99*cation_radius_angstrom^7.76)",
        "source_doi": "10.1103/PhysRevB.110.014502",
        "units": {
            "radii": "angstrom",
            "t1": "electronvolt"
        }
    }

@app.get("/materials")
def list_materials():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT cation, anion, x, nelect, anion_radius, cation_radius, abs_t1
        FROM cuprates
        ORDER BY anion, cation, x
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "cation": r[0],
            "anion": r[1],
            "x": r[2],
            "nelect": r[3],
            "anion_radius": r[4],
            "cation_radius": r[5],
            "abs_t1_eV": r[6]
        }
        for r in rows
    ]

@app.get("/nearest_reference")
def nearest_reference(cation_radius: float, anion_radius: float, limit: int = 5):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT cation, anion, x, anion_radius, cation_radius, abs_t1,
               ((anion_radius - ?) * (anion_radius - ?) +
                (cation_radius - ?) * (cation_radius - ?)) AS distance2
        FROM cuprates
        ORDER BY distance2 ASC
        LIMIT ?
    """, (anion_radius, anion_radius, cation_radius, cation_radius, limit))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "cation": r[0],
            "anion": r[1],
            "x": r[2],
            "anion_radius": r[3],
            "cation_radius": r[4],
            "abs_t1_eV": r[5],
            "distance2": r[6]
        }
        for r in rows
    ]
