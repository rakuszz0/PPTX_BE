from __future__ import annotations
from typing import List
from uuid import uuid4
import re

from app.domain.courses.models import (
    CourseDocument, CourseModule, ContentSection, ContentType, RegType,
)
from app.core.errors import ExtractionError
from app.core.logging import get_logger

from .base import CourseExtractor, _cache_get, _cache_put, _sha256, validate_url

logger = get_logger(__name__)


class WizapeExtractor(CourseExtractor):
    def __init__(self, use_cache: bool = True, max_retries: int = 2, timeout_s: int = 20):
        self.use_cache = use_cache
        self.max_retries = max_retries
        self.timeout_s = timeout_s

    def extract(self, url: str) -> CourseDocument:
        url = validate_url(url)
        cache_key = f"wizape_course_{_sha256(url)}"
        if self.use_cache:
            cached = _cache_get(cache_key)
            if cached:
                try:
                    return CourseDocument.model_validate(cached)
                except Exception as exc:
                    logger.warning("cache invalid, ignoring: %s", exc)

        course = self._build_demo_course(url)

        if self.use_cache:
            _cache_put(cache_key, course.to_dict())
        return course

    def _build_demo_course(self, url: str) -> CourseDocument:
        course_id = f"course_{_sha256(url)[:12]}"
        modules = self._detect_and_build_modules(url, course_id)
        return CourseDocument(
            id=course_id,
            title="Kepatuhan Regulasi untuk Perangkat Medis",
            source_url=url,
            description="Kursus komprehensif tentang regulasi perangkat medis di Indonesia: definisi, klasifikasi risiko, kerangka hukum, alur registrasi, ISO 13485, dan kewajiban pasca pemasaran.",
            modules=modules,
            author="WIZAPE Academy \u2014 Tim Kedokteran & Regulatori",
            metadata={"source": "wizape_extractor_mock", "modules_detected": len(modules)},
        )

    def _detect_and_build_modules(self, url: str, course_id: str) -> List[CourseModule]:
        module_plan = self._discover_modules(url)
        modules = []
        for idx, meta in enumerate(module_plan, start=1):
            mid = f"mod_{course_id}_{idx:03d}"
            sections = self._build_module_sections(idx, mid)
            word_count = sum(len(s.text.split()) for s in sections)
            modules.append(CourseModule(
                id=mid,
                module_number=idx,
                title=meta["title"],
                summary=meta["summary"],
                sections=sections,
                source_url=meta.get("source_url") or url,
                word_count=word_count,
                metadata={"intro": meta.get("intro", "")},
            ))
        return modules

    def _discover_modules(self, url: str) -> list[dict]:
        plan = [
            {
                "title": "Pengantar Regulasi Perangkat Medis",
                "summary": "Pengertian, tujuan, dan ruang lingkup regulasi perangkat medis di Indonesia beserta gambaran ekosistem.",
                "intro": "Pembukaan kursus: mengapa regulasi menjadi tulang punggung keselamatan pasien dan kepercayaan publik.",
            },
            {
                "title": "Definisi dan Klasifikasi Kelas Risiko",
                "summary": "Membedah definisi perangkat medis dan sistem klasifikasi risiko kelas A, B, C, D beserta contoh.",
                "intro": "Klasifikasi yang tepat adalah titik awal perencanaan registrasi dan mutu.",
            },
            {
                "title": "Kerangka Hukum dan Badan Regulatori",
                "summary": "Ulasan UU Kesehatan, Permenkes, dan peran Kementerian Kesehatan dalam pengawasan alat kesehatan.",
                "intro": "Dari hierarki peraturan hingga wewenang otoritas.",
            },
            {
                "title": "Alur Registrasi dan Izin Edar",
                "summary": "Tahapan pra-registrasi, evaluasi, sampai dengan terbitnya Sertifikat Izin Edar.",
                "intro": "Bagaimana sebuah perangkat medis dilegalkan untuk beredar.",
            },
            {
                "title": "ISO 13485 dan Sistem Manajemen Mutu",
                "summary": "Standar manajemen mutu khusus industri perangkat medis dan implikasi implementasinya.",
                "intro": "Membangun budaya mutu yang konsisten.",
            },
            {
                "title": "Pelabelan, Iklan, dan Promosi",
                "summary": "Persyaratan label: informasi, bahasa, serta aturan promosi dan iklan yang etis.",
                "intro": "Komunikasi yang akurat dan bertanggung jawab.",
            },
            {
                "title": "Pasca Pemasaran dan Vigilansi",
                "summary": "PMS, pelaporan kejadian tidak diinginkan, FSCA, serta peran recall dalam pengawasan.",
                "intro": "Kewajiban setelah izin edar diterbitkan.",
            },
            {
                "title": "Audit dan Kepatuhan",
                "summary": "Jenis audit, kesiapan produsen, dan praktik kepatuhan berkelanjutan.",
                "intro": "Menjaga kinerja sistem di atas kertas.",
            },
            {
                "title": "Perangkat Lunak Medis dan AI",
                "summary": "Klasifikasi SaMD (Software as a Medical Device) dan algoritma AI sebagai perangkat medis.",
                "intro": "Menjawab tantangan digitalisasi.",
            },
            {
                "title": "Studi Kasus dan Praktik Terbaik",
                "summary": "Contoh kasus riil: registrasi, penyelesaian temuan audit, dan strategi recall.",
                "intro": "Belajar dari pengalaman lapangan.",
            },
        ]
        dynamic_count = self._dynamic_count_from_url(url, default=len(plan))
        return plan[:dynamic_count]

    def _dynamic_count_from_url(self, url: str, default: int) -> int:
        m = re.search(r"modules?[=/:_-](\d+)", url, flags=re.I)
        if m:
            try:
                n = int(m.group(1))
                return max(1, min(n, 50))
            except Exception:
                return default
        return default

    def _build_module_sections(self, module_number: int, module_id: str) -> List[ContentSection]:
        builders = {
            1: self._sections_module_01,
            2: self._sections_module_02,
            3: self._sections_module_03,
            4: self._sections_module_04,
            5: self._sections_module_05,
            6: self._sections_module_06,
            7: self._sections_module_07,
            8: self._sections_module_08,
            9: self._sections_module_09,
            10: self._sections_module_10,
        }
        fn = builders.get(module_number, self._sections_module_generic)
        sections = fn(module_id, module_number)
        for i, s in enumerate(sections):
            if not s.id:
                s.id = f"{module_id}_sec_{i+1:02d}"
            if s.order == 0:
                s.order = i + 1
        return sections

    def _sec(self, title: str, text: str, ctype: ContentType = ContentType.SECTION,
             reg: RegType | None = None, ref: str | None = None, idx: int = 0) -> ContentSection:
        return ContentSection(
            id=f"gen_{uuid4().hex[:8]}",
            title=title,
            content_type=ctype,
            reg_type=reg,
            text=text,
            subsections=[],
            source_ref=ref,
            order=idx,
        )

    def _sections_module_01(self, mid: str, n: int) -> List[ContentSection]:
        return [
            self._sec("Tujuan Modul",
                      "Setelah mempelajari Modul 1 ini, peserta diharapkan mampu menjelaskan tujuan regulasi perangkat medis, "
                      "memahami pihak-pihak yang terlibat, dan menerjemahkan urgensi kepatuhan dalam praktik sehari-hari.",
                      ContentType.SECTION, RegType.EXPLANATION, f"{mid}.sec_01", 1),
            self._sec("Latar Belakang",
                      "Perangkat medis yang beredar di Indonesia berjumlah sangat beragam, mulai dari alat sederhana seperti termometer "
                      "sampai teknologi tinggi seperti MRI dan perangkat lunak medis berbasis kecerdasan buatan. Keberagaman ini menuntut "
                      "kerangka pengaturan yang mampu menjamin keamanan, khasiat/efektivitas, dan mutu tanpa menghambat inovasi. "
                      "Negara-negara anggota WHO telah menyepakati Model List of Essential Medicines dan Essential Medical Devices "
                      "sebagai acuan dasar untuk menjamin ketersediaan alat yang aman, terjangkau, dan tepat guna. "
                      "Pengalaman regional menunjukkan bahwa pengawasan yang lemah dapat berakibat pada produk yang tidak memenuhi syarat, "
                      "kejadian tidak diinginkan pada pasien, dan hilangnya kepercayaan masyarakat terhadap sistem kesehatan.",
                      ContentType.SECTION, RegType.FACT, f"{mid}.sec_02", 2),
            self._sec("Tujuan Regulasi Perangkat Medis",
                      "Secara umum, regulasi perangkat medis mempunyai empat tujuan utama:\n"
                      "1. Melindungi pasien dan pengguna dari risiko yang tidak dapat diterima.\n"
                      "2. Menjamin kebenaran, kecukupan, dan keandalan informasi yang disampaikan produsen.\n"
                      "3. Menciptakan lapangan persaingan usaha yang sehat dan setara bagi pelaku industri.\n"
                      "4. Mendukung inovasi yang bertanggung jawab melalui jalur regulasi yang jelas dan dapat diikuti.",
                      ContentType.LIST, RegType.REGULATORY_REQUIREMENT, f"{mid}.sec_03", 3),
            self._sec("Pihak Terkait dalam Ekosistem",
                      "Ekosistem perangkat medis melibatkan produsen (pabrikan/importir/distributor), tenaga kesehatan, pasien, "
                      "otoritas regulator (Kementerian Kesehatan, Badan Pengawas Obat dan Makanan jika diperlukan), "
                      "asosiasi profesi, serta lembaga sertifikasi dan laboratorium uji. "
                      "Kolaborasi antar pihak sangat penting: produsen mengajukan bukti ilmiah dan teknis, tenaga medis "
                      "memberikan masukan penggunaan klinis, dan regulator melakukan evaluasi independen.",
                      ContentType.PARAGRAPH, RegType.EXPLANATION, f"{mid}.sec_04", 4),
            self._sec("Prinsip Dasar Pengaturan",
                      "Prinsip yang harus selalu dipegang dalam setiap aspek regulasi adalah proporsionalitas (sesuai risiko), "
                      "transparansi (dapat diikuti dan dipahami), konsistensi (tidak berubah-ubah), akuntabilitas, dan "
                      "berbasis bukti (evidence-based decision making). Prinsip ini akan tercermin pada cara klasifikasi, "
                      "alur registrasi, serta pengawasan pasca pemasaran.",
                      ContentType.CALLOUT, RegType.INTERPRETATION, f"{mid}.sec_05", 5),
            self._sec("Kesimpulan Pendahuluan",
                      "Modul berikutnya akan menjelaskan definisi dan klasifikasi yang akan menentukan tingkat pengawasan. "
                      "Pahami dengan baik karena hampir seluruh proses administratif dan teknis dimulai dari penentuan kelas risiko yang tepat.",
                      ContentType.SECTION, RegType.EXPLANATION, f"{mid}.sec_06", 6),
        ]

    def _sections_module_02(self, mid: str, n: int) -> List[ContentSection]:
        return [
            self._sec("Tinjauan", "Definisi perangkat medis mengikuti acuan internasional (GHTF, IMDRF) yang kemudian diadaptasi "
                                  "dalam peraturan nasional.", ContentType.SECTION, RegType.EXPLANATION, f"{mid}.sec_01", 1),
            self._sec("Definisi Formal",
                      "Perangkat medis adalah instrumen, aparatus, mesin, implan, reagen in-vitro, perangkat lunak, bahan, atau "
                      "artikel lain yang digunakan pada manusia untuk salah satu tujuan berikut: diagnosis, pencegahan, pemantauan, "
                      "pengobatan atau peredaan penyakit; investigasi, penggantian, atau modifikasi anatomi atau proses fisiologis; "
                      "pengendalian kehamilan; serta dukungan atau penyokong kehidupan. Ciri khas: efek utama yang diinginkan TIDAK "
                      "dicapai dengan cara farmakologis, imunologis, atau metabolisme, meskipun cara tersebut dapat membantu.",
                      ContentType.HEADING, RegType.FACT, f"{mid}.sec_02", 2),
            self._sec("Membedakan dengan Obat",
                      "Jika efek utama produk dicapai melalui mekanisme farmakologis pada reseptor atau proses metabolik, produk "
                      "tersebut dikategorikan sebagai obat atau biologis. Sebaliknya, jika mekanisme utamanya fisik, mekanik, termal, "
                      "radiasi, atau elektrikal, maka termasuk perangkat medis. Beberapa produk kombinasi memiliki jalur khusus dan "
                      "harus dikonsultasikan lebih lanjut ke otoritas.",
                      ContentType.PARAGRAPH, RegType.INTERPRETATION, f"{mid}.sec_03", 3),
            self._sec("Prinsip Klasifikasi Berbasis Risiko",
                      "Risiko adalah fungsi dari tingkat keparahan bahaya, durasi kontak dengan tubuh, status invasif, serta apakah "
                      "alat aktif mengirimkan energi atau obat. Semakin besar potensi bahaya, semakin tinggi kelas dan semakin ketat "
                      "persyaratan evaluasi serta audit.",
                      ContentType.PARAGRAPH, RegType.EXPLANATION, f"{mid}.sec_04", 4),
            self._sec("Kelas A \u2014 Risiko Rendah",
                      "Alat tanpa kontak dengan pasien atau kontak sesaat pada kulit yang utuh, misalnya: kasa steril sekali pakai, "
                      "alat bantu jalan non-invasif, peralatan fisioterapi yang tidak menembus kulit.",
                      ContentType.SECTION, RegType.EXAMPLE, f"{mid}.sec_05", 5),
            self._sec("Kelas B \u2014 Risiko Sedang",
                      "Kontak sementara dengan jaringan, selaput lendir, atau invasif singkat. Contoh: jarum suntik, spuit, "
                      "termometer elektronik, perban kontak luka, kateter urin jangka pendek.",
                      ContentType.SECTION, RegType.EXAMPLE, f"{mid}.sec_06", 6),
            self._sec("Kelas C \u2014 Risiko Tinggi",
                      "Perangkat invasif jangka pendek atau aktif yang mengirimkan energi dengan bahaya potensial. Contoh: kateter "
                      "intravaskuler jangka pendek, alat laser bedah, alat anestesi, monitor fisiologis kritis.",
                      ContentType.SECTION, RegType.EXAMPLE, f"{mid}.sec_07", 7),
            self._sec("Kelas D \u2014 Risiko Sangat Tinggi",
                      "Perangkat invasif jangka panjang atau yang secara langsung menunjang kehidupan (life-supporting/life-sustaining). "
                      "Contoh: stent koroner, katup jantung prostetik, sendi buatan implan, IVD yang menguji darah manusia untuk "
                      "penyakit menular kritis, pacemaker.",
                      ContentType.SECTION, RegType.EXAMPLE, f"{mid}.sec_08", 8),
            self._sec("Matriks Keputusan Klasifikasi",
                      "Dalam praktik, klasifikasi ditentukan melalui matriks aturan yang memperhitungkan invasif, durasi kontak, "
                      "aktif vs non-aktif, bagian tubuh yang terkontak, dan apakah alat mengandung zat obat. "
                      "Baca panduan klasifikasi resmi otoritas dan dokumentasikan rationale klasifikasi Anda.",
                      ContentType.CALLOUT, RegType.REGULATORY_REQUIREMENT, f"{mid}.sec_09", 9),
        ]

    def _sections_module_03(self, mid: str, n: int) -> List[ContentSection]:
        return [
            self._sec("Dasar Hukum", "Hierarki peraturan di Indonesia dimulai dari UUD 1945, UU, Peraturan Pemerintah, "
                                     "Peraturan Presiden, hingga Peraturan Menteri Kesehatan.",
                      ContentType.REGULATION, RegType.FACT, f"{mid}.sec_01", 1),
            self._sec("Undang-Undang Kesehatan",
                      "UU tentang Kesehatan mengatur secara umum hak dan kewajiban dalam pelayanan kesehatan, termasuk jaminan "
                      "keamanan dan mutu sediaan farmasi dan alat kesehatan.",
                      ContentType.SECTION, RegType.REGULATORY_REQUIREMENT, f"{mid}.sec_02", 2),
            self._sec("Peraturan Menteri Kesehatan",
                      "Permenkes menjadi instrumen teknis utama yang mengatur detail klasifikasi, registrasi, pelabelan, "
                      "pengawasan, dan vigilansi perangkat medis. Ikuti versi terbaru karena regulasi berkembang mengikuti "
                      "kemajuan teknologi dan harmonisasi standar regional.",
                      ContentType.SECTION, RegType.REGULATORY_REQUIREMENT, f"{mid}.sec_03", 3),
            self._sec("Peran Kementerian Kesehatan",
                      "Kementerian Kesehatan menyelenggarakan kebijakan nasional, melakukan evaluasi registrasi, pengawasan "
                      "distribusi, serta pengelolaan sistem informasi alat kesehatan. Setiap tahapan didukung oleh pedoman dan "
                      "petunjuk teknis.",
                      ContentType.PARAGRAPH, RegType.EXPLANATION, f"{mid}.sec_04", 4),
            self._sec("Badan Sertifikasi dan Akreditasi",
                      "Lembaga sertifikasi penilai kesesuaian ISO 13485 harus terakreditasi; laboratorium uji juga harus memiliki "
                      "akreditasi yang relevan sesuai parameter yang diuji. Produsen bertanggung jawab memastikan lembaga yang dipilih memiliki kewenangan.",
                      ContentType.PARAGRAPH, RegType.REGULATORY_REQUIREMENT, f"{mid}.sec_05", 5),
        ]

    def _sections_module_04(self, mid: str, n: int) -> List[ContentSection]:
        return [
            self._sec("Ringkasan Alur", "Registrasi adalah proses evaluasi administratif dan teknis untuk memutuskan kelayakan izin edar.",
                      ContentType.SECTION, RegType.EXPLANATION, f"{mid}.sec_01", 1),
            self._sec("Tahap 1: Pra-Registrasi",
                      "Sebelum pengajuan formal, produsen perlu melakukan: (1) self-assessment klasifikasi; "
                      "(2) menyiapkan bukti kinerja dan keamanan (literatur, uji klinis bila perlu); "
                      "(3) memastikan SMM sudah berjalan sesuai target sertifikasi; "
                      "(4) menyiapkan draf label dan informasi pengguna.",
                      ContentType.PARAGRAPH, RegType.REGULATORY_REQUIREMENT, f"{mid}.sec_02", 2),
            self._sec("Tahap 2: Pengajuan dan Pembayaran",
                      "Melalui portal resmi otoritas, produsen mengunggah dokumen, mengisi formulir deskripsi produk, dan "
                      "melunasi biaya pengujian/evaluasi sesuai kelas. Pastikan kelengkapan administrasi agar tidak dikembalikan pada tahap awal.",
                      ContentType.PARAGRAPH, RegType.REGULATORY_REQUIREMENT, f"{mid}.sec_03", 3),
            self._sec("Tahap 3: Evaluasi Administratif dan Teknis",
                      "Petugas memeriksa kelengkapan dan konsistensi dokumen. Jika kurang, klarifikasi diminta dalam batas waktu. "
                      "Untuk kelas tinggi, evaluasi teknis mendalam dapat melibatkan reviewer ahli klinis/teknik serta audit lapang.",
                      ContentType.PARAGRAPH, RegType.EXPLANATION, f"{mid}.sec_04", 4),
            self._sec("Tahap 4: Penerbitan Izin Edar",
                      "Jika lulus evaluasi, diterbitkan Sertifikat Izin Edar (SIE) dengan masa berlaku tertentu. Produsen wajib "
                      "menampilkan nomor SIE dalam label dan materi promosi sesuai aturan.",
                      ContentType.PARAGRAPH, RegType.REGULATORY_REQUIREMENT, f"{mid}.sec_05", 5),
            self._sec("Perubahan Setelah Izin Edar",
                      "Setiap perubahan desain, bahan, label, atau indikasi memerlukan notifikasi atau pengajuan perubahan izin. "
                      "Jangan mengubah tanpa memastikan kebutuhan regulasi telah dipenuhi.",
                      ContentType.CALLOUT, RegType.INTERPRETATION, f"{mid}.sec_06", 6),
        ]

    def _sections_module_05(self, mid: str, n: int) -> List[ContentSection]:
        return [
            self._sec("Apa itu ISO 13485?",
                      "ISO 13485 adalah standar internasional Sistem Manajemen Mutu yang khusus untuk organisasi di rantai pasok "
                      "perangkat medis. Berlaku untuk desain, produksi, instalasi, dan servis.",
                      ContentType.SECTION, RegType.FACT, f"{mid}.sec_01", 1),
            self._sec("Konteks Organisasi dan Risk-Based Thinking",
                      "Identifikasi risiko yang relevan dengan mutu dan keselamatan pasien; terapkan pemikiran berbasis risiko pada "
                      "seluruh proses. Pendekatan ini juga sejalan dengan pedoman manajemen risiko ISO 14971.",
                      ContentType.PARAGRAPH, RegType.EXPLANATION, f"{mid}.sec_02", 2),
            self._sec("Proses Utama",
                      "Pengembangan desain dan pengembangan (DHF/DMR), pengendalian dokumen dan catatan, pembelian dan kendali pemasok, "
                      "produksi, sterilisasi, validasi proses, penanganan komplain, CAPA, audit internal, serta tinjauan manajemen.",
                      ContentType.LIST, RegType.EXPLANATION, f"{mid}.sec_03", 3),
            self._sec("Traceability",
                      "Kemampuan menelusur (traceability) mulai dari komponen baku sampai unit yang terpasang pada pasien adalah "
                      "keharusan untuk investigasi recall dan kaji-ulang keamanan.",
                      ContentType.PARAGRAPH, RegType.REGULATORY_REQUIREMENT, f"{mid}.sec_04", 4),
            self._sec("Siklus Sertifikasi",
                      "Sertifikat biasanya berlaku 3 tahun dengan audit survailans setiap tahunnya. Kesiapan dokumen dan konsistensi "
                      "implementasi sangat menentukan hasil audit.",
                      ContentType.PARAGRAPH, RegType.EXPLANATION, f"{mid}.sec_05", 5),
        ]

    def _sections_module_06(self, mid: str, n: int) -> List[ContentSection]:
            return [
            self._sec("Prinsip Pelabelan",
                      "Label harus akurat, tidak menyesatkan, dan memuat semua informasi yang dibutuhkan pengguna.",
                      ContentType.SECTION, RegType.REGULATORY_REQUIREMENT, f"{mid}.sec_01", 1),
            self._sec("Bahasa dan Informasi Wajib",
                      "Label perangkat medis di Indonesia minimal menyertakan Bahasa Indonesia. Informasi yang harus ada: nama "
                      "dagang/nama generik, produsen/importir, nomor izin edar, nomor batch/lot, tanggal kedaluwarsa, indikasi, "
                      "kontraindikasi, peringatan, dan cara penyimpanan.",
                      ContentType.PARAGRAPH, RegType.REGULATORY_REQUIREMENT, f"{mid}.sec_02", 2),
            self._sec("Iklan dan Promosi",
                      "Promosi dan iklan tidak boleh menyampaikan klaim yang melampaui indikasi yang disetujui dalam izin edar. "
                      "Semua pernyataan khasiat harus didukung bukti ilmiah dan ditulis secara etis.",
                      ContentType.PARAGRAPH, RegType.REGULATORY_REQUIREMENT, f"{mid}.sec_03", 3),
            self._sec("Pembatasan Khusus",
                      "Beberapa perangkat tertentu hanya boleh dipromosikan kepada tenaga kesehatan yang memenuhi kualifikasi; "
                      "diskusikan dengan tim legal/regulatory sebelum menerbitkan materi promosi.",
                      ContentType.CALLOUT, RegType.INTERPRETATION, f"{mid}.sec_04", 4),
        ]

    def _sections_module_07(self, mid: str, n: int) -> List[ContentSection]:
        return [
            self._sec("Mengapa Pasca Pemasaran Penting?",
                      "Pengalaman penggunaan pada populasi nyata dapat mengungkap kejadian yang tidak muncul pada studi klinis "
                      "berukuran terbatas.",
                      ContentType.SECTION, RegType.EXPLANATION, f"{mid}.sec_01", 1),
            self._sec("Post-Market Surveillance (PMS)",
                      "Produsen wajib menyusun dan memelihara rencana PMS: mengumpulkan data keluhan, publikasi ilmiah, "
                      "dan pengalaman pengguna; kemudian menganalisis secara sistematis.",
                      ContentType.PARAGRAPH, RegType.REGULATORY_REQUIREMENT, f"{mid}.sec_02", 2),
            self._sec("Pelaporan Kejadian Tidak Diinginkan",
                      "Setiap kejadian yang dapat menyebabkan atau berpotensi menyebabkan kematian atau kerusakan kesehatan serius "
                      "harus dilaporkan ke otoritas dalam jangka waktu yang ditentukan.",
                      ContentType.PARAGRAPH, RegType.REGULATORY_REQUIREMENT, f"{mid}.sec_03", 3),
            self._sec("FSCA & Recall",
                      "FSCA (Field Safety Corrective Action) mencakup recall produk, notifikasi pengguna, modifikasi label atau "
                      "perangkat lunak, serta penghentian penjualan. Rencanakan komunikasi dan logistik dengan matang.",
                      ContentType.PARAGRAPH, RegType.REGULATORY_REQUIREMENT, f"{mid}.sec_04", 4),
        ]

    def _sections_module_08(self, mid: str, n: int) -> List[ContentSection]:
        return [
            self._sec("Jenis Audit", "Internal, eksternal (sertifikasi), dan audit dari otoritas.",
                      ContentType.SECTION, RegType.EXPLANATION, f"{mid}.sec_01", 1),
            self._sec("Kesiapan Audit",
                      "Pastikan dokumen mutu terkendali, catatan lengkap, CAPA tertutup, personel memahami prosedur, dan area produksi "
                      "sesuai tata laksana ruang.",
                      ContentType.PARAGRAPH, RegType.EXPLANATION, f"{mid}.sec_02", 2),
            self._sec("Penanganan Temuan",
                      "Klasifikasikan temuan, tentukan akar permasalahan, susun rencana aksi perbaikan dan pencegahan (CAPA) dengan "
                      "batas waktu yang realistis.",
                      ContentType.PARAGRAPH, RegType.EXPLANATION, f"{mid}.sec_03", 3),
        ]

    def _sections_module_09(self, mid: str, n: int) -> List[ContentSection]:
        return [
            self._sec("SaMD dan AI",
                      "Perangkat lunak yang dimaksudkan untuk tujuan medis (Software as a Medical Device / SaMD) diklasifikasikan "
                      "menggunakan aturan khusus. Semakin tinggi dampak pada kondisi pasien, semakin tinggi kelasnya.",
                      ContentType.SECTION, RegType.EXPLANATION, f"{mid}.sec_01", 1),
            self._sec("Risiko AI/ML",
                      "Algoritma yang dapat berubah setelah pemasaran (adaptive AI) membutuhkan rencana perubahan terkendali dan "
                      "monitor kinerja berkelanjutan guna memastikan tidak terjadi penyimpangan performa.",
                      ContentType.CALLOUT, RegType.INTERPRETATION, f"{mid}.sec_02", 2),
        ]

    def _sections_module_10(self, mid: str, n: int) -> List[ContentSection]:
        return [
            self._sec("Pendekatan Studi Kasus",
                      "Setiap kasus diawali dengan pengenalan konteks, identifikasi masalah, analisis akar, serta usulan tindakan.",
                      ContentType.SECTION, RegType.EXPLANATION, f"{mid}.sec_01", 1),
            self._sec("Kasus 1: Registrasi Alat Diagnostik",
                      "Tugas: tim Anda harus mengajukan izin edar untuk IVD baru. Buatlah daftar periksa dokumen dan tahapan evaluasi.",
                      ContentType.CALLOUT, RegType.EXAMPLE, f"{mid}.sec_02", 2),
            self._sec("Kasus 2: Investigasi Komplain dan Recall",
                      "Tugas: merespons temuan 20 unit alat infus yang menunjukkan alarm gagal. Buat tahapan investigasi dan keputusan FSCA.",
                      ContentType.CALLOUT, RegType.EXAMPLE, f"{mid}.sec_03", 3),
        ]

    def _sections_module_generic(self, mid: str, n: int) -> List[ContentSection]:
        return [
            self._sec(f"Ringkasan Modul {n}",
                      f"Modul {n} menyediakan bahan lanjutan untuk memperdalam materi kursus kepatuhan regulasi.",
                      ContentType.SECTION, RegType.EXPLANATION, f"{mid}.sec_01", 1),
            self._sec("Materi Pembelajaran",
                      "Bacalah tujuan pembelajaran di awal modul. Kerjakan latihan dan refleksi di akhir agar dapat menghubungkan "
                      "dengan kasus nyata di tempat kerja Anda.",
                      ContentType.PARAGRAPH, RegType.EXPLANATION, f"{mid}.sec_02", 2),
            self._sec("Referensi",
                      "Gunakan sumber primer (peraturan, pedoman teknis) dan hindari hanya mengandalkan ringkasan dari pihak ketiga.",
                      ContentType.SECTION, RegType.FACT, f"{mid}.sec_03", 3),
        ]
