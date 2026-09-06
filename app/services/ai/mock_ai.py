from __future__ import annotations
from typing import List
from uuid import uuid4

from app.domain.courses.models import CourseModule, ContentSection
from app.domain.presentation.ai_pipeline import (
    ContentAnalysis, ContentTopic, EducationalDesign, LearningObjective,
    PresentationStory, StoryBeat, SlideBlueprint, BlueprintSlide, VisualPlan,
    AIPipelineResult,
)
from .provider import (
    AIContentAnalyst, AIEducationalDesigner, AIStoryArchitect,
    AISlideArchitect, AIVisualDesigner,
)


class MockContentAnalyst(AIContentAnalyst):
    def analyze(self, module: CourseModule) -> ContentAnalysis:
        text_all = self._flatten_text(module.sections)
        words = text_all.split()
        topics = self._extract_topics(module)
        regulatory = self._extract_regulatory(module)
        return ContentAnalysis(
            module_id=module.id,
            title=module.title,
            summary=module.summary or self._derive_summary(module),
            topics=topics,
            key_concepts=[t.name for t in topics],
            regulatory_items=regulatory,
            difficulty="intermediate",
            target_audience="profesional medis dan staf regulatori",
            prerequisites=["Pemahaman dasar tentang industri perangkat medis",
                           "Pengetahuan umum tentang sistem kesehatan di Indonesia"],
            estimated_reading_time_min=max(8, len(words) // 130),
            word_count=len(words),
            metadata={"source": "mock_analyst", "topics_detected": len(topics)},
        )

    def _flatten_text(self, sections: List[ContentSection]) -> str:
        parts = []
        for s in sections:
            if s.title:
                parts.append(s.title)
            if s.text:
                parts.append(s.text)
            if s.subsections:
                parts.append(self._flatten_text(s.subsections))
        return "\n".join(parts)

    def _extract_topics(self, module: CourseModule) -> List[ContentTopic]:
        mapping = [
            ("Pengantar dan Ruang Lingkup", "Pendahuluan regulasi perangkat medis: lingkup, definisi, dan tujuan.", 0.7, "INTRODUCTION",
             ["regulasi", "perangkat medis", "definisi", "tujuan", "lingkup"]),
            ("Definisi dan Klasifikasi", "Klasifikasi perangkat medis berdasarkan risiko: Kelas A, B, C, D.", 0.95, "CONCEPT",
             ["klasifikasi", "risiko", "kelas A", "kelas B", "kelas C", "kelas D", "definisi"]),
            ("Regulasi di Indonesia", "Kerangka hukum: Permenkes, UU Kesehatan, Peraturan Kemenkes, dan badan regulatori.", 0.95, "REGULATION",
             ["permenkes", "uu kesehatan", "kemenkes", "badan regulasi", "hukum", "peraturan"]),
            ("Proses Registrasi dan Izin Edar", "Alur registrasi: pra-registrasi, uji klinis, evaluasi, dan izin edar.", 0.92, "PROCESS",
             ["registrasi", "izin edar", "uji klinis", "evaluasi", "alur"]),
            ("Persyaratan Sistem Manajemen Mutu", "ISO 13485:2016 dan penerapan QMS untuk produsen perangkat medis.", 0.85, "EXPLANATION",
             ["iso 13485", "smm", "qms", "mutu", "manajemen mutu"]),
            ("Pelabelan dan Iklan", "Persyaratan informasi label, bahasa, dan aturan promosi/iklan perangkat medis.", 0.78, "REGULATION",
             ["pelabelan", "label", "iklan", "promosi", "informasi", "bahasa"]),
            ("Pasca Pemasaran (Post-Market Surveillance)", "PMS, vigilansi, pelaporan kejadian tidak diinginkan, dan recall.", 0.9, "EXPLANATION",
             ["pms", "vigilansi", "post-market", "recall", "kejadian tidak diinginkan", "pelaporan"]),
            ("Studi Kasus", "Contoh implementasi: produk diagnostik in-vitro dan alat bedah.", 0.7, "CASE_STUDY",
             ["studi kasus", "contoh", "ivd", "alat bedah", "implementasi"]),
            ("Ringkasan", "Poin-poin kunci dan implikasi praktis untuk tenaga profesional.", 0.6, "SUMMARY",
             ["ringkasan", "kunci", "praktis", "kesimpulan"]),
            ("Kuesioner & Diskusi", "Formatif quiz dan diskusi refleksi penerapan.", 0.4, "QUIZ",
             ["kuis", "pertanyaan", "diskusi", "refleksi"]),
        ]
        title_low = module.title.lower()
        result = []
        for name, desc, importance, purpose, keywords in mapping:
            score = 0.5
            for kw in keywords:
                if kw in title_low or any(kw in (s.text or "").lower() for s in module.sections):
                    score += 0.05
            result.append(ContentTopic(
                id=f"topic_{uuid4().hex[:8]}",
                name=name,
                description=desc,
                importance=min(1.0, importance * score),
                keywords=keywords,
                suggested_slide_purpose=purpose,
            ))
        result.sort(key=lambda t: t.importance, reverse=True)
        return result[:8]

    def _extract_regulatory(self, module: CourseModule) -> list[dict]:
        return [
            {"id": "reg_001", "type": "REGULATORY_REQUIREMENT",
             "title": "Peraturan Menteri Kesehatan tentang Perangkat Medis",
             "ref": "Permenkes No. 1188/Menkes/Per/VIII/2010",
             "priority": "high"},
            {"id": "reg_002", "type": "REGULATORY_REQUIREMENT",
             "title": "ISO 13485:2016 Sistem Manajemen Mutu",
             "ref": "ISO 13485:2016",
             "priority": "high"},
            {"id": "reg_003", "type": "REGULATORY_REQUIREMENT",
             "title": "Kewajiban Pelaporan Pasca Pemasaran",
             "ref": "Permenkes tentang Vigilansi Perangkat Medis",
             "priority": "critical"},
        ]

    def _derive_summary(self, module: CourseModule) -> str:
        if module.sections:
            t = module.sections[0].text
            if len(t) > 300:
                return t[:297] + "..."
            return t or f"Ringkasan modul: {module.title}"
        return f"Ringkasan modul: {module.title}"


class MockEducationalDesigner(AIEducationalDesigner):
    def design(self, module: CourseModule, analysis: ContentAnalysis) -> EducationalDesign:
        objectives = [
            LearningObjective(
                id=f"lo_{uuid4().hex[:6]}",
                text="Menjelaskan definisi, ruang lingkup, dan tujuan regulasi perangkat medis di Indonesia.",
                bloom_level="understand",
            ),
            LearningObjective(
                id=f"lo_{uuid4().hex[:6]}",
                text="Mengklasifikasikan perangkat medis berdasarkan kelas risiko (A, B, C, D) beserta contohnya.",
                bloom_level="analyze",
            ),
            LearningObjective(
                id=f"lo_{uuid4().hex[:6]}",
                text="Menganalisis alur proses registrasi dan izin edar perangkat medis.",
                bloom_level="analyze",
            ),
            LearningObjective(
                id=f"lo_{uuid4().hex[:6]}",
                text="Menerapkan persyaratan sistem manajemen mutu ISO 13485 pada konteks produsen perangkat medis.",
                bloom_level="apply",
            ),
            LearningObjective(
                id=f"lo_{uuid4().hex[:6]}",
                text="Mengevaluasi kewajiban pasca pemasaran (PMS, vigilansi, dan pelaporan kejadian).",
                bloom_level="evaluate",
            ),
        ]
        return EducationalDesign(
            module_id=module.id,
            title=module.title,
            learning_objectives=objectives,
            pedagogical_approach="expository with case-based learning",
            assessment_strategy="formatif dengan kuis dan refleksi",
            recommended_structure=[
                {"type": "TITLE", "section": "cover"},
                {"type": "SECTION", "section": "intro"},
                {"type": "OBJECTIVES", "section": "tujuan"},
                {"type": "CONCEPT", "section": "konsep"},
                {"type": "REGULATION", "section": "regulasi"},
                {"type": "PROCESS", "section": "alur"},
                {"type": "COMPARISON", "section": "klasifikasi"},
                {"type": "EXPLANATION", "section": "iso"},
                {"type": "EXPLANATION", "section": "post-market"},
                {"type": "CASE_STUDY", "section": "contoh"},
                {"type": "SUMMARY", "section": "ringkasan"},
                {"type": "QUIZ", "section": "kuis"},
            ],
            instructional_sequence=[
                {"step": 1, "activity": "Apersepsi: relevansi regulasi bagi praktisi", "duration_min": 2},
                {"step": 2, "activity": "Paparan konsep definisi dan klasifikasi", "duration_min": 8},
                {"step": 3, "activity": "Diskusi terarah: uji pemahaman kelas risiko", "duration_min": 5},
                {"step": 4, "activity": "Paparan regulasi dan alur registrasi", "duration_min": 12},
                {"step": 5, "activity": "Studi kasus: aplikasi pada contoh nyata", "duration_min": 8},
                {"step": 6, "activity": "Studi kasus: pasca pemasaran", "duration_min": 5},
                {"step": 7, "activity": "Ringkasan, refleksi, dan kuis formatif", "duration_min": 5},
            ],
            common_misconceptions=[
                "Semua perangkat medis hanya perlu satu jenis izin.",
                "Regulasi hanya berlaku untuk perangkat berisiko tinggi.",
                "Izin edar berarti tidak ada lagi kewajiban setelah pemasaran.",
            ],
            real_world_connections=[
                "Proses registrasi alat diagnostik di Pusat Registrasi Alat Kesehatan.",
                "Contoh recall alat medis dan peran vigilansi masyarakat.",
                "Penerapan label bilingual pada perangkat medis.",
            ],
        )


class MockStoryArchitect(AIStoryArchitect):
    def build_story(self, module: CourseModule, analysis: ContentAnalysis,
                    design: EducationalDesign, target_slides: int = 12) -> PresentationStory:
        return PresentationStory(
            module_id=module.id,
            title=module.title,
            hook="Perangkat medis yang aman dan efektif dimulai dari pemahaman regulasi yang benar. Setiap tenaga medis dan profesional di ekosistem kesehatan perlu mengetahui kerangka kerja yang melindungi pasien dan menjamin kualitas.",
            narrative_arc="problem-regulation-application-reflection",
            beats=[
                StoryBeat(id=f"beat_{uuid4().hex[:6]}", beat_type="opening",
                          title="Salam dan Konteks",
                          narrative="Kenali mengapa regulasi perangkat medis ada dan apa pengaruhnya bagi kita sehari-hari.",
                          emotional_arc="curious", duration_slide_range=(1, 2)),
                StoryBeat(id=f"beat_{uuid4().hex[:6]}", beat_type="exposition",
                          title="Definisi dan Klasifikasi Risiko",
                          narrative="Pahami peta konsep: apa yang disebut perangkat medis, dan bagaimana sistem kelas risiko A/B/C/D bekerja.",
                          emotional_arc="informative", duration_slide_range=(3, 4)),
                StoryBeat(id=f"beat_{uuid4().hex[:6]}", beat_type="exposition",
                          title="Peta Regulasi dan Alur Registrasi",
                          narrative="Dari UU hingga izin edar: telusuri tahapan yang harus dilalui produsen.",
                          emotional_arc="structured", duration_slide_range=(5, 6)),
                StoryBeat(id=f"beat_{uuid4().hex[:6]}", beat_type="climax",
                          title="Persyaratan Mutu dan Kewajiban Pasca Pemasaran",
                          narrative="ISO 13485 dan kewajiban PMS menjadi titik kritis: apa yang harus dijaga setelah produk beredar.",
                          emotional_arc="engaged", duration_slide_range=(7, 9)),
                StoryBeat(id=f"beat_{uuid4().hex[:6]}", beat_type="transition",
                          title="Studi Kasus Terpandu",
                          narrative="Hubungkan teori dengan contoh produk yang riil di lapangan.",
                          emotional_arc="applied", duration_slide_range=(10, 10)),
                StoryBeat(id=f"beat_{uuid4().hex[:6]}", beat_type="closing",
                          title="Ringkasan dan Refleksi",
                          narrative="Tutup dengan poin kunci, cek pemahaman, dan pesan takeaway yang berkesan.",
                          emotional_arc="reflective", duration_slide_range=(11, 12)),
            ],
            opening_message="Selamat datang di Modul 1: Kepatuhan Regulasi untuk Perangkat Medis.",
            closing_message="Dengan memahami regulasi, anda menjadi garda terdepan keselamatan pasien.",
            target_slide_count=target_slides,
        )


class MockSlideArchitect(AISlideArchitect):
    def build_blueprint(self, module: CourseModule, analysis: ContentAnalysis,
                        design: EducationalDesign, story: PresentationStory,
                        min_slides: int = 10, max_slides: int = 12) -> SlideBlueprint:
        count = max(min_slides, min(max_slides, 11))
        slides: List[BlueprintSlide] = []

        slides.append(BlueprintSlide(
            id=f"bp_{uuid4().hex[:8]}", slide_number=len(slides) + 1,
            purpose="INTRODUCTION", layout="TITLE",
            title="Kepatuhan Regulasi untuk Perangkat Medis",
            main_message="Panduan terstruktur untuk profesional kesehatan dan perangkat medis",
            components=[
                {"type": "HEADING", "area": "title", "content": {"text": "Kepatuhan Regulasi untuk Perangkat Medis"}},
                {"type": "SUBTITLE", "area": "subtitle", "content": {"text": f"{module.title} \u2022 Modul 1 \u2022 Dikti & Klinis"}},
                {"type": "BADGE", "area": "meta", "content": {"text": "SlideForge \u2022 Medical Theme", "variant": "pill"}},
            ],
            source_references=["module_01.title"],
        ))

        slides.append(BlueprintSlide(
            id=f"bp_{uuid4().hex[:8]}", slide_number=len(slides) + 1,
            purpose="AGENDA", layout="AGENDA",
            title="Agenda Pembelajaran",
            main_message="Alur belajar dari pengenalan hingga refleksi",
            components=[
                {"type": "HEADING", "area": "heading", "content": {"text": "Agenda Pembelajaran"}},
                {"type": "BULLET_LIST", "area": "item_1",
                 "items": [{"text": "Pendahuluan: mengapa regulasi ada", "level": 0}]},
                {"type": "BULLET_LIST", "area": "item_2",
                 "items": [{"text": "Definisi & klasifikasi perangkat medis (Kelas A\u2013D)", "level": 0}]},
                {"type": "BULLET_LIST", "area": "item_3",
                 "items": [{"text": "Kerangka regulasi Indonesia & alur registrasi", "level": 0}]},
                {"type": "BULLET_LIST", "area": "item_4",
                 "items": [{"text": "ISO 13485 & kewajiban pasca pemasaran", "level": 0}]},
                {"type": "BULLET_LIST", "area": "item_5",
                 "items": [{"text": "Studi kasus, ringkasan & refleksi", "level": 0}]},
            ],
        ))

        slides.append(BlueprintSlide(
            id=f"bp_{uuid4().hex[:8]}", slide_number=len(slides) + 1,
            purpose="OBJECTIVES", layout="OBJECTIVES",
            title="Tujuan Pembelajaran",
            main_message="Setelah modul ini, peserta mampu menjelaskan, mengklasifikasikan, menganalisis, menerapkan, dan mengevaluasi.",
            components=[
                {"type": "HEADING", "area": "heading", "content": {"text": "Tujuan Pembelajaran"}},
                {"type": "CARD", "area": "objective_1", "variant": "card_primary",
                 "heading": "Menjelaskan", "content": {"heading": "Menjelaskan", "text": "Definisi, lingkup, dan tujuan regulasi perangkat medis."}},
                {"type": "CARD", "area": "objective_2", "variant": "card_teal",
                 "heading": "Mengklasifikasikan", "content": {"heading": "Mengklasifikasikan", "text": "Kelas risiko A, B, C, D beserta contoh produk masing-masing."}},
                {"type": "CARD", "area": "objective_3", "variant": "card_success",
                 "heading": "Menganalisis", "content": {"heading": "Menganalisis & Menerapkan", "text": "Alur registrasi, izin edar, dan penerapan ISO 13485."}},
            ],
            source_references=["module_01.section_01"],
        ))

        slides.append(BlueprintSlide(
            id=f"bp_{uuid4().hex[:8]}", slide_number=len(slides) + 1,
            purpose="CONCEPT", layout="THREE_CARD",
            title="Apa itu Perangkat Medis?",
            main_message="Perangkat medis mencakup instrumen, mesin, implan, reagen in-vitro, dan aksesoris yang digunakan untuk tujuan medis.",
            components=[
                {"type": "HEADING", "area": "heading", "content": {"text": "Apa itu Perangkat Medis?"}},
                {"type": "CARD", "area": "card_1", "variant": "card",
                 "content": {"heading": "Definisi", "text": "Instrumen, aparatus, mesin, implan, reagen in-vitro, perangkat lunak, atau bahan lain yang digunakan untuk diagnosis, pencegahan, pemantauan, pengobatan, atau rehabilitasi penyakit."}},
                {"type": "CARD", "area": "card_2", "variant": "card",
                 "content": {"heading": "Bukan Obat", "text": "Cara kerjanya tidak melalui farmakologis, imunologis, atau metabolisme. Jika efek utamanya dicapai secara fisik, mekanik, atau elektrik \u2192 perangkat medis."}},
                {"type": "CARD", "area": "card_3", "variant": "card",
                 "content": {"heading": "Contoh", "text": "Termometer, tensimeter, alat USG, stent jantung, prostetik, IVD (reagen tes cepat), MRI, perangkat lunak medis."}},
            ],
            speaker_notes=["Sumber: Definisi mengacu pada Permenkes dan panduan WHO/IMDRF categorization."],
            source_references=["module_01.section_02", "reg_001"],
        ))

        slides.append(BlueprintSlide(
            id=f"bp_{uuid4().hex[:8]}", slide_number=len(slides) + 1,
            purpose="CONCEPT", layout="COMPARISON",
            title="Klasifikasi Kelas Risiko",
            main_message="Empat kelas risiko \u2014 dari rendah (A) sampai sangat tinggi (D) \u2014 menentukan ketatnya persyaratan.",
            components=[
                {"type": "HEADING", "area": "heading", "content": {"text": "Klasifikasi Kelas Risiko"}},
                {"type": "CARD", "area": "left_header", "variant": "card_success",
                 "content": {"heading": "Risiko Rendah \u2192 Sedang", "text": ""}},
                {"type": "CARD", "area": "right_header", "variant": "card_danger",
                 "content": {"heading": "Risiko Tinggi \u2192 Sangat Tinggi", "text": ""}},
                {"type": "CARD", "area": "left_row_1", "variant": "card_success",
                 "content": {"heading": "Kelas A (Risiko Rendah)", "text": "Alat tanpa kontak tubuh / kontak sesaat. Contoh: kasa steril sekali pakai, bedah kertas, alat fisioterapi non-invasif."}},
                {"type": "CARD", "area": "right_row_1", "variant": "card_warning",
                 "content": {"heading": "Kelas C (Risiko Tinggi)", "text": "Perangkat invasif jangka pendek atau aktif mengirim energi. Contoh: kateter jantung, alat laser bedah, monitor pasien."}},
                {"type": "CARD", "area": "left_row_2", "variant": "card_teal",
                 "content": {"heading": "Kelas B (Risiko Sedang)", "text": "Kontak tubuh sementara / invasif singkat. Contoh: termometer elektronik, alat suntik, spuit, dressing luka."}},
                {"type": "CARD", "area": "right_row_2", "variant": "card_danger",
                 "content": {"heading": "Kelas D (Risiko Sangat Tinggi)", "text": "Alat yang menunjang/sustaining hidup, implan jangka panjang. Contoh: stent koroner, prostetik sendi, IVD darah manusia."}},
                {"type": "CALLOUT", "area": "left_row_3",
                 "content": {"text": "Kelas menentukan: dokumentasi yang harus disiapkan, uji klinis yang diperlukan, dan proses audit registrasi."}},
                {"type": "BADGE", "area": "right_row_3", "variant": "pill",
                 "content": {"text": "Regulasi: Permenkes Tentang Klasifikasi"}},
            ],
            source_references=["module_01.section_02", "reg_001"],
        ))

        slides.append(BlueprintSlide(
            id=f"bp_{uuid4().hex[:8]}", slide_number=len(slides) + 1,
            purpose="PROCESS", layout="PROCESS",
            title="Alur Registrasi & Izin Edar",
            main_message="Sebelum beredar, setiap perangkat medis melalui tahapan pra-registrasi, evaluasi teknis, dan pemberian izin edar.",
            components=[
                {"type": "HEADING", "area": "heading", "content": {"text": "Alur Registrasi & Izin Edar"}},
                {"type": "CARD", "area": "step_1", "variant": "card_primary",
                 "content": {"heading": "1. Pra-Registrasi", "text": "Klasifikasi produk, persiapan dokumen mutu & bukti kinerja, serta pendaftaran akun."}},
                {"type": "CARD", "area": "step_2", "variant": "card_teal",
                 "content": {"heading": "2. Pengajuan", "text": "Unggah dokumen: Technical File (STED), ISO 13485, uji klinis (bila diminta), dan pelabelan."}},
                {"type": "CARD", "area": "step_3", "variant": "card_success",
                 "content": {"heading": "3. Evaluasi", "text": "Review administratif, evaluasi kesesuaian, klarifikasi, dan/atau audit lapang jika diperlukan."}},
                {"type": "CARD", "area": "step_4", "variant": "card_warning",
                 "content": {"heading": "4. Izin Edar", "text": "Diterbitkan Sertifikat Izin Edar (SIE) dengan masa berlaku tertentu. Produsen wajib menjaga pasca pemasaran."}},
            ],
            source_references=["module_01.section_03", "reg_001"],
        ))

        slides.append(BlueprintSlide(
            id=f"bp_{uuid4().hex[:8]}", slide_number=len(slides) + 1,
            purpose="EXPLANATION", layout="TEXT_VISUAL",
            title="Sistem Manajemen Mutu ISO 13485:2016",
            main_message="ISO 13485 adalah standar SMM khusus untuk organisasi di rantai pasok perangkat medis; fokus pada keselamatan pasien dan konsistensi proses.",
            components=[
                {"type": "HEADING", "area": "heading", "content": {"text": "ISO 13485:2016 \u2022 Sistem Manajemen Mutu"}},
                {"type": "BULLET_LIST", "area": "text",
                 "items": [
                     {"text": "Berbasis proses PDCA & Risk-based thinking", "level": 0},
                     {"text": "Mencakup desain & pengembangan, pembelian, produksi, kontrol pengukuran", "level": 0},
                     {"text": "Wajib terdokumentasi dan diaudit internal + sertifikasi badan", "level": 0},
                     {"text": "Kewajiban terkait: traceability, kontrol dokumen, penanganan komplain", "level": 0},
                     {"text": "Menjadi prasyarat utama pengajuan registrasi Kelas C dan D", "level": 0},
                 ]},
                {"type": "METRIC", "area": "visual",
                 "content": {"label": "Prasyarat Sertifikasi Kelas Tinggi", "value": "ISO 13485"}},
            ],
            source_references=["module_01.section_04", "reg_002"],
        ))

        slides.append(BlueprintSlide(
            id=f"bp_{uuid4().hex[:8]}", slide_number=len(slides) + 1,
            purpose="EXPLANATION", layout="TWO_COLUMN",
            title="Kewajiban Pasca Pemasaran",
            main_message="Pemasaran hanya permulaan. Produsen berkewajiban terus memantau keamanan dan kinerja produk.",
            components=[
                {"type": "HEADING", "area": "heading", "content": {"text": "Kewajiban Pasca Pemasaran (Post-Market)"}},
                {"type": "CARD", "area": "left", "variant": "card_primary",
                 "content": {"heading": "PMS & Vigilansi", "text": "Program Post-Market Surveillance (PMS), pengumpulan data pengalaman lapangan, pelaporan kejadian tidak diinginkan (Adverse Event) ke otoritas."}},
                {"type": "CARD", "area": "right", "variant": "card_danger",
                 "content": {"heading": "Field Safety Corrective Action", "text": "Jika ditemukan risiko: FSCA (Recall, notifikasi pengguna, modifikasi instruksi). Semua harus terdokumentasi dan dilaporkan tepat waktu."}},
            ],
            speaker_notes=["Penting ditekankan: produsen bertanggung jawab selama masa pakai produk berada di pasar."],
            source_references=["module_01.section_05", "reg_003"],
        ))

        slides.append(BlueprintSlide(
            id=f"bp_{uuid4().hex[:8]}", slide_number=len(slides) + 1,
            purpose="CASE_STUDY", layout="CASE_STUDY",
            title="Studi Kasus Terpandu",
            main_message="Terapkan teori regulasi dan klasifikasi pada dua kasus sederhana berikut.",
            components=[
                {"type": "HEADING", "area": "heading", "content": {"text": "Studi Kasus Terpandu"}},
                {"type": "CARD", "area": "scenario", "variant": "card_teal",
                 "content": {"heading": "Skenario", "text": "Sebuah klinik berencana mengimpor (1) rapid tes antigen COVID-19 (IVD) dan (2) kateter urin sekali pakai. Identifikasi kelas masing-masing dan prasyarat utama sebelum peredaran."}},
                {"type": "CARD", "area": "problem", "variant": "card_warning",
                 "content": {"heading": "Analisis Klasifikasi", "text": "Rapid tes antigen tergolong IVD. Kateter urin adalah perangkat invasif kontak sementara (Kelas B). Tentukan jalur dokumen dan persyaratan evaluasi."}},
                {"type": "CARD", "area": "solution", "variant": "card_success",
                 "content": {"heading": "Jawaban & Diskusi", "text": "IVD dapat risiko menengah/tinggi. Keduanya perlu Izin Edar: technical file, bukti kinerja, label Bahasa Indonesia, serta kewajiban PMS setelah beredar."}},
            ],
            source_references=["module_01.section_06"],
        ))

        slides.append(BlueprintSlide(
            id=f"bp_{uuid4().hex[:8]}", slide_number=len(slides) + 1,
            purpose="SUMMARY", layout="SUMMARY",
            title="Ringkasan Modul",
            main_message="Tiga pesan kunci: pahami kelas risiko, ikuti alur registrasi yang benar, dan rawat kewajiban pasca pemasaran.",
            components=[
                {"type": "HEADING", "area": "heading", "content": {"text": "Ringkasan Modul"}},
                {"type": "CARD", "area": "point_1", "variant": "card_primary",
                 "content": {"heading": "Klasifikasi = Risiko", "text": "Kelas A/B/C/D membedakan intensitas pengawasan: semakin tinggi risiko, semakin ketat prasyarat dan audit."}},
                {"type": "CARD", "area": "point_2", "variant": "card_teal",
                 "content": {"heading": "Registrasi bukan \"sekadar admin\"", "text": "Persiapan mutu (ISO 13485), technical file, dan bukti kinerja adalah proses substantif yang melindungi pasien."}},
                {"type": "CARD", "area": "point_3", "variant": "card_success",
                 "content": {"heading": "Kewajiban berlanjut setelah beredar", "text": "PMS, vigilansi, dan FSCA harus menjadi budaya organisasi, bukan sekadar formalitas."}},
            ],
        ))

        slides.append(BlueprintSlide(
            id=f"bp_{uuid4().hex[:8]}", slide_number=len(slides) + 1,
            purpose="QUIZ", layout="QUIZ",
            title="Refleksi & Kuis Formatif",
            main_message="Uji pemahaman Anda sebelum lanjut ke modul berikutnya.",
            components=[
                {"type": "HEADING", "area": "heading", "content": {"text": "Refleksi & Kuis Formatif"}},
                {"type": "PARAGRAPH", "area": "question",
                 "content": {"text": "Perangkat yang termasuk invasif, kontak dengan jaringan tubuh lebih dari 30 hari, dan berpotensi menunjang kehidupan, termasuk kelas risiko mana?"}},
                {"type": "CARD", "area": "option_A", "variant": "card", "content": {"heading": "A", "text": "Kelas A (risiko rendah)"}},
                {"type": "CARD", "area": "option_B", "variant": "card", "content": {"heading": "B", "text": "Kelas B (risiko sedang)"}},
                {"type": "CARD", "area": "option_C", "variant": "card_success", "content": {"heading": "C", "text": "Kelas D (risiko sangat tinggi) \u2713"}},
                {"type": "CARD", "area": "option_D", "variant": "card", "content": {"heading": "D", "text": "Tidak perlu diklasifikasikan jika alat impor"}},
            ],
            speaker_notes=["Jawaban yang benar: C. Perangkat invasif jangka panjang yang mendukung kehidupan masuk Kelas D."],
        ))

        while len(slides) < count:
            slides.append(BlueprintSlide(
                id=f"bp_{uuid4().hex[:8]}", slide_number=len(slides) + 1,
                purpose="TAKEAWAY", layout="TAKEAWAY",
                title="Takeaway",
                main_message="Kepatuhan regulasi adalah upaya bersama menjaga kepercayaan dan keselamatan pasien.",
                components=[
                    {"type": "HEADING", "area": "heading", "content": {"text": "Takeaway"}},
                    {"type": "QUOTE", "area": "point_1",
                     "content": {"text": "Regulasi bukanlah penghalang inovasi \u2014 melainkan pagar yang menjaga agar inovasi tetap aman, efektif, dan dapat dipercaya oleh masyarakat.", "author": "Prinsip Dasar Pengaturan Alat Kesehatan"}},
                    {"type": "CARD", "area": "point_2", "variant": "card_primary",
                     "content": {"heading": "Next Step", "text": "Pelajari Modul 2: Pedoman Teknis Klasifikasi dan Alur Registrasi yang lebih mendalam."}},
                    {"type": "CARD", "area": "point_3", "variant": "card_teal",
                     "content": {"heading": "Kontak", "text": "Tim SlideForge siap membantu pembahasan kasus dan pendalaman materi lebih lanjut."}},
                ],
            ))

        return SlideBlueprint(
            module_id=module.id,
            title=module.title,
            slides=slides[:count],
            metadata={"provider": "mock_ai", "slides_requested": count},
        )


class MockVisualDesigner(AIVisualDesigner):
    def plan_visuals(self, module: CourseModule, blueprint: SlideBlueprint,
                     theme_name: str = "medical_professional") -> VisualPlan:
        return VisualPlan(
            module_id=module.id,
            theme_name=theme_name,
            color_scheme={
                "primary": "#165DFF",
                "accent_teal": "#0CB0A9",
                "success": "#2BA471",
                "warning": "#D48806",
                "danger": "#D9363E",
                "neutral_900": "#0E1B2D",
            },
            typography={"family_sans": "Calibri", "family_serif": "Georgia"},
            visual_emphasis={
                "title_slide": "accent_band",
                "data_slides": "cards_and_metrics",
                "case_study": "callout_based",
            },
            icon_plan=[
                {"slide_purpose": "PROCESS", "icon_set": "sequential_steps"},
                {"slide_purpose": "REGULATION", "icon_set": "shields_stamps"},
            ],
            asset_plan=[
                {"type": "placeholder", "for": "TEXT_VISUAL:visual", "format": "shape_with_metric"},
            ],
        )


class MockAIPipelineRunner:
    def __init__(self, theme_name: str = "medical_professional"):
        self.theme_name = theme_name

    def run(self, module: CourseModule, min_slides: int = 10, max_slides: int = 12) -> AIPipelineResult:
        analyst = MockContentAnalyst()
        educational = MockEducationalDesigner()
        story_architect = MockStoryArchitect()
        slide_architect = MockSlideArchitect()
        visual = MockVisualDesigner()

        analysis = analyst.analyze(module)
        design = educational.design(module, analysis)
        story = story_architect.build_story(module, analysis, design, target_slides=max_slides)
        blueprint = slide_architect.build_blueprint(module, analysis, design, story,
                                                    min_slides=min_slides, max_slides=max_slides)
        visual_plan = visual.plan_visuals(module, blueprint, self.theme_name)

        return AIPipelineResult(
            module_id=module.id,
            analysis=analysis,
            educational_design=design,
            story=story,
            blueprint=blueprint,
            visual_plan=visual_plan,
        )
