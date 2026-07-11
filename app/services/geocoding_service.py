"""
Reverse Geocoding Service
Mengambil provinsi/kabupaten/kecamatan/desa dari koordinat latitude & longitude
menggunakan Nominatim (OpenStreetMap) - gratis, tanpa API key.

Docs: https://nominatim.org/release-docs/latest/api/Reverse/
"""
import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

# Nominatim usage policy mewajibkan User-Agent yang jelas
# (https://operations.osmfoundation.org/policies/nominatim/)
HEADERS = {
    "User-Agent": "SilaseZ-App/1.0 (https://github.com/; contact: admin@silasez.local)"
}


def reverse_geocode(latitude: float, longitude: float) -> dict:
    """
    Return dict: provinsi, kabupaten, kecamatan, desa, alamat_lengkap
    Raise ValueError kalau gagal / lokasi tidak ditemukan.
    """
    params = {
        "lat": latitude,
        "lon": longitude,
        "format": "jsonv2",
        "addressdetails": 1,
        "accept-language": "id",
    }

    try:
        response = httpx.get(
            NOMINATIM_URL,
            params=params,
            headers=HEADERS,
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise ValueError(f"Gagal melakukan reverse geocoding: {e}")

    data = response.json()
    address = data.get("address")

    if not address:
        raise ValueError(
            "Lokasi tidak ditemukan untuk koordinat tersebut. "
            "Pastikan latitude/longitude valid."
        )

    provinsi = address.get("state", "-")

    kabupaten = (
        address.get("county")
        or address.get("city")
        or address.get("city_district")
        or "-"
    )

    kecamatan = (
        address.get("suburb")
        or address.get("district")
        or address.get("municipality")
        or "-"
    )

    desa = (
        address.get("village")
        or address.get("hamlet")
        or address.get("neighbourhood")
        or "-"
    )

    return {
        "provinsi": provinsi,
        "kabupaten": kabupaten,
        "kecamatan": kecamatan,
        "desa": desa,
        "alamat_lengkap": data.get("display_name"),
    }
