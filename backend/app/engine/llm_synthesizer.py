import httpx
import logging
from app.core.config import settings

logger = logging.getLogger("llm_synthesizer")

def build_local_fallback_narrative(agent_id: str, entity_code: str, data: dict, raw_context: str) -> str:
    """Menghasilkan narasi korespondensi profesional berbasis payload deterministik tanpa LLM."""
    aid = agent_id.lower()

    if aid == "agent_1":
        if data.get("catalog_matched"):
            return (
                f"[{entity_code}] REKOMENDASI PENAWARAN HARGA RESMI ({raw_context}):\n"
                f"Berdasarkan katalog master price PS03 terverifikasi, harga pokok unit tercatat sebesar "
                f"${data.get('unit_cost', 0):.2f}. Mengacu pada target margin {data.get('target_margin_pct', 18.0)}%, "
                f"harga jual penawaran resmi yang disarankan ke pelanggan adalah sebesar ${data.get('recommended_quote_price', 0):.2f}. "
                f"Draf penawaran siap diteruskan ke bagian Sales Operation."
            )
        else:
            return (
                f"[{entity_code}] PERMINTAAN SOURCING PARALEL VENDOR ({raw_context}):\n"
                f"Part number tidak terdaftar pada katalog aktif PS03. Direkomendasikan melakukan pengiriman RFQ paralel "
                f"ke 3 vendor terakreditasi di kawasan Asia Pasifik untuk mendapatkan harga terbaik dalam waktu 24 jam."
            )

    elif aid == "agent_2":
        margin = data.get("gross_margin_pct", 0)
        remedy = data.get("remedy")
        if data.get("is_margin_breached") or data.get("is_moq_breached"):
            remedy_text = ""
            if remedy:
                remedy_text = (
                    f" Rekomendasi penyesuaian: Tingkatkan kuantitas pesanan ke batas MOQ {remedy.get('suggested_qty')} unit "
                    f"untuk mendapatkan harga tier-2 (${remedy.get('tier_price'):.2f}), memproyeksikan margin pulih menjadi "
                    f"{remedy.get('projected_margin'):.2f}% dengan buffer stock {remedy.get('buffer_stock_qty')} unit."
                )
            return (
                f"[{entity_code}] PERINGATAN KONTRAK MARGIN & MOQ ({raw_context}):\n"
                f"Kalkulasi margin kotor terdeteksi sebesar {margin:.2f}% (ambang batas min 15.0%). "
                f"Status: Margin Breach = {data.get('is_margin_breached')}, MOQ Breach = {data.get('is_moq_breached')}."
                f"{remedy_text} Persetujuan diperlukan sebelum membuka kuncian PO."
            )
        else:
            return (
                f"[{entity_code}] VALIDASI KONTRAK SO/PO BERSIH ({raw_context}):\n"
                f"Margin kotor dihitung sebesar {margin:.2f}% (memenuhi standar min 15.0%) dan kuantitas memenuhi ambang MOQ. "
                f"Pesanan pembelian siap disetujui tanpa penyesuaian."
            )

    elif aid == "agent_3":
        return (
            f"[{entity_code}] ESKALASI BACKLOG PENGIRIMAN ({raw_context}):\n"
            f"Terdeteksi deviasi keterlambatan kedatangan selama {data.get('delta_days', 0)} hari dari target RDD. "
            f"Tingkat keparahan backlog dinilai: {data.get('severity', 'NORMAL')}. Total nilai pesanan terdampak: "
            f"${data.get('order_value', 0):,.2f}. Disarankan koordinasi darurat dengan ekspedisi/forwarder."
        )

    elif aid == "agent_4":
        return (
            f"[{entity_code}] PEMBERITAHUAN JATUH TEMPO MASTER PRICE ({raw_context}):\n"
            f"Part {data.get('part_number')} dengan harga saat ini ${data.get('current_cost', 0):.2f} {data.get('currency')} "
            f"akan kedaluwarsa pada {data.get('valid_until')}. Disarankan penyesuaian indeks inflasi sebesar "
            f"+{data.get('recommended_inflation_adjustment_pct', 2.1)}% untuk pembaruan kontrak periode berikutnya."
        )

    elif aid == "agent_5":
        return (
            f"[{entity_code}] SCORECARD EVALUASI PEMASOK ({raw_context}):\n"
            f"Skor komposit performa supplier tercatat sebesar {data.get('composite_score', 0):.1f}/100. "
            f"Klasifikasi tiering: {data.get('vendor_tier')}. Berdasarkan kebijakan pengadaan, alokasi kuota yang disarankan "
            f"adalah sebesar {data.get('suggested_allocation_pct', 0)}% dari total volume batch."
        )

    elif aid == "agent_6":
        return (
            f"[{entity_code}] PENERIMAAN GUDANG & NOTA RETUR RMA ({raw_context}):\n"
            f"Dari total penerimaan {data.get('scanned_total', 0)} unit, tercatat {data.get('valid_gr_qty', 0)} unit valid "
            f"untuk penerbitan Partial GR dan {data.get('damaged_qty', 0)} unit barang rusak. "
            f"Draf nota debit RMA sebesar ${data.get('debit_claim_amount', 0):,.2f} otomatis disiapkan ke vendor."
        )

    elif aid == "agent_7":
        if "days_left" in data:
            return (
                f"[{entity_code}] RADAR JATUH TEMPO PINJAMAN STOK ({raw_context}):\n"
                f"Masa peminjaman stok antar-mitra tersisa {data.get('days_left', 0)} hari lagi. "
                f"Tindakan yang direkomendasikan: {data.get('action_required')}. Segera kirimkan surat konfirmasi pengembalian barang."
            )
        else:
            return (
                f"[{entity_code}] SINKRONISASI TRIANGLE TRADE (BRD 6.3) ({raw_context}):\n"
                f"Proof of Delivery (POD) forwarder telah terverifikasi ({data.get('pod_verified')}). "
                f"Logical GR ({data.get('po_reference')}) dan Logical GI ({data.get('so_reference')}) siap diposting secara sinkron "
                f"tanpa mutasi fisik pada gudang hub Singapura."
            )

    elif aid == "agent_8":
        return (
            f"[{entity_code}] JURNAL REKONSILIASI KURS VALAS ({raw_context}):\n"
            f"Pencocokan mutasi bank mencatat nilai buku ${data.get('book_value', 0):,.2f} vs nilai settlement ${data.get('settle_value', 0):,.2f}. "
            f"Selisih kurs sebesar ${abs(data.get('fx_variance', 0)):,.2f} dialokasikan ke akun buku besar {data.get('allocated_account')} "
            f"({data.get('fx_type')}) mata uang dasar {data.get('currency_base')}."
        )

    elif aid == "agent_9":
        return (
            f"[{entity_code}] RADAR LIKUIDITAS & RUNWAY KAS OPERASIONAL ({raw_context}):\n"
            f"Kas efektif bersih terhitung sebesar ${data.get('net_usable_cash', 0):,.2f} dengan estimasi ketahanan runway "
            f"{data.get('weeks_runway', 0):.1f} minggu. Status likuiditas: {data.get('liquidity_status')}. "
            f"Pemberitahuan darurat ke CFO: {data.get('alert_treasury_lead')}."
        )

    return (
        f"[{entity_code}] ADVISORY DETERMINISTIK ({raw_context}):\n"
        f"Kalkulasi terverifikasi Python: {data}. Menunggu otorisasi PIC sebelum eksekusi."
    )

async def generate_grounded_draft(agent_id: str, entity_code: str, deterministic_data: dict, raw_context: str) -> str:
    """Sintesis bahasa alami dengan Claude API grounded pada JSON deterministik, dengan fallback lokal tahan banting."""
    api_key = (settings.ANTHROPIC_API_KEY or "").strip()

    # Jika API key kosong atau masih bernilai placeholder dummy
    if not api_key or api_key in ("your_anthropic_api_key_here", "none", "null"):
        return build_local_fallback_narrative(agent_id, entity_code, deterministic_data, raw_context)

    system_prompt = (
        "Anda adalah AI Orchestrator untuk Batu Networks ERP. "
        "Gunakan HANYA data deterministik yang disediakan. Jangan mengarang angka atau persentase di luar JSON. "
        "Format teks harus profesional, padat, dan langsung menyajikan rekomendasi tindakan serta draf korespondensi resmi."
    )

    user_content = (
        f"Agen: {agent_id}\n"
        f"Entitas: {entity_code}\n"
        f"Data Kalkulasi: {deterministic_data}\n"
        f"Konteks Tambahan: {raw_context}"
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": settings.DEFAULT_LLM_MODEL,
                    "max_tokens": 500,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_content}]
                }
            )
            if response.status_code == 200:
                res_json = response.json()
                return res_json["content"][0]["text"]
            else:
                logger.warning(f"[LLM] Anthropic API returned HTTP {response.status_code}. Fallback ke narasi lokal.")
                return build_local_fallback_narrative(agent_id, entity_code, deterministic_data, raw_context)
    except Exception as err:
        logger.warning(f"[LLM] Gagal menghubungi Anthropic API ({type(err).__name__}). Menggunakan narasi deterministik lokal.")
        return build_local_fallback_narrative(agent_id, entity_code, deterministic_data, raw_context)