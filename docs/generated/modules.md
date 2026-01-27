# Module Reference

> Automatisch generiert am 2026-01-27 12:58

## 📁 (root)

### `app.py`
*549 Zeilen*

**Key Imports:** bonsai_disce_tree, disce_core, streamlit

---

### `bonsai_disce_tree.py`
*411 Zeilen*

**Klassen:**
- `TreeOptions` → (keine Methoden)
- `State` → (keine Methoden)
- `Segment` → (keine Methoden)

**Funktionen:** `_clamp()`, `_lerp()`, `_safe_dim()`, `options_from_dims()`, `expand_lsystem()`, `_draw_tree()`, `_draw_leaves()`, `diff_factor_from_opts()` ... (+1)

**Key Imports:** dataclasses, math, matplotlib, random

---

### `bonsai_lsystem.py`
*342 Zeilen*

**Klassen:**
- `LSystemBonsaiParams` → (keine Methoden)

**Funktionen:** `_clamp()`, `_lerp()`, `_safe_dim()`, `params_from_dims()`, `build_lsystem_string()`, `_draw_bonsai_from_string()`, `generate_bonsai_figure()`

**Key Imports:** dataclasses, math, matplotlib

---

### `bonsai_space_colonization.py`
*435 Zeilen*

**Klassen:**
- `Attractor` → (keine Methoden)
- `Branch` → (keine Methoden)
- `BonsaiParams` → (keine Methoden)

**Funktionen:** `_normalize()`, `_lerp()`, `_params_from_metrics()`, `_generate_bonsai_attractors()`, `_initialize_trunk()`, `_grow_tree()`, `_draw_bonsai()`, `generate_bonsai_figure()`

**Key Imports:** dataclasses, math, matplotlib, random

---

### `build_merlin_csv.py`
*58 Zeilen*

**Key Imports:** pandas

---

### `calibrate_merlin.py`
*166 Zeilen*

**Funktionen:** `analyze_text()`, `main()`

**Key Imports:** features_viewer, pandas, sklearn

---

### `disce_core.py`
*499 Zeilen*

**Funktionen:** `build_sentence_data()`, `select_hotspots()`, `build_metrics_summary()`, `build_disce_metrics()`, `analyze_text_for_ui()`, `analyze_text_for_llm()`

**Key Imports:** features_viewer

---

### `features_demo.py`
*323 Zeilen*

**Funktionen:** `read_text_from_file()`, `mean()`, `tokenize_and_split()`, `pos_tag_sentences()`, `count_tokens()`, `check_grammar_with_languagetool()`, `sentence_lengths()`, `finite_verbs_per_sentence()` ... (+4)

**Key Imports:** HanTa, requests, somajo

---

### `features_viewer.py`
*1865 Zeilen*

**Funktionen:** `read_text_from_file()`, `mean()`, `clamp01()`, `tokenize_and_split()`, `pos_tag_sentences()`, `count_tokens()`, `check_grammar_with_languagetool()`, `sentence_lengths()` ... (+27)

**Key Imports:** HanTa, requests, somajo, spacy, wordfreq

---

### `generate_docs.py`
*408 Zeilen*
> generate_docs.py - Automatische Repo-Dokumentation für Disce/Kleiner Bär

**Funktionen:** `should_ignore()`, `get_tree_structure()`, `analyze_python_file()`, `detect_integrations()`, `generate_repo_map()`, `generate_modules_doc()`, `generate_integrations_doc()`, `main()`

**Key Imports:** argparse, ast, collections

---

### `grammar_demo.py`
*85 Zeilen*

**Funktionen:** `read_text_from_file()`, `tokenize_and_split()`, `check_grammar_with_languagetool()`, `count_tokens()`

**Key Imports:** requests, somajo

---

### `lemma_demo.py`
*61 Zeilen*

**Funktionen:** `read_text_from_file()`, `tokenize_and_split()`, `lemmatize_tokens()`

**Key Imports:** simplemma, somajo

---

### `openai_services.py`
*111 Zeilen*
> OpenAI-Integration für Großer Bär

**Funktionen:** `get_openai_client()`, `transcribe_audio()`, `generate_coach_feedback()`, `check_api_connection()`

**Key Imports:** grosser_baer, openai, streamlit, tempfile

---

### `pos_demo.py`
*170 Zeilen*

**Funktionen:** `read_text_from_file()`, `tokenize_and_split()`, `pos_tag_sentences()`, `sentence_lengths()`, `finite_verbs_per_sentence()`, `estimated_subclauses()`, `complex_nps_per_sentence()`, `mean()`

**Key Imports:** HanTa, somajo

---

### `tokenize_demo.py`
*37 Zeilen*

**Funktionen:** `tokenize_and_split()`, `read_text_from_file()`

**Key Imports:** somajo

---

## 📁 config

### `config\app_config.py`
*202 Zeilen*
> App Configuration für Großer Bär

**Funktionen:** `init_app_config()`, `get_config()`, `set_config()`, `is_mock_mode()`, `is_debug_mode()`, `should_skip_pretest()`, `is_airtable_enabled()`, `log_event()` ... (+6)

**Key Imports:** streamlit

---

### `config\pretest_loader.py`
*526 Zeilen*
> Pretest Loader für Großer Bär

**Funktionen:** `load_pretest_config()`, `get_enabled_modules()`, `get_module_by_id()`, `init_pretest_state()`, `save_response()`, `get_response()`, `check_show_condition()`, `render_single_select()` ... (+12)

**Key Imports:** streamlit

---

## 📁 grosser_baer

### `grosser_baer\__init__.py`
*57 Zeilen*
> Großer Bär – Speaking Coach Modul für Disce.

**Key Imports:** audio_handler, feedback_generator, prompts, session_logger, task_templates

---

### `grosser_baer\audio_handler.py`
*651 Zeilen*
> Audio-Handling für Großer Bär.

**Klassen:**
- `TranscriptResult` → from_text
- `ProsodyResult` → to_dict
- `AudioAnalysisResult` → text, word_count
- `AudioProcessor` → __init__, process, transcribe_only

**Funktionen:** `count_fillers()`, `mock_transcribe()`, `mock_analyze_prosody()`, `get_azure_credentials()`, `azure_transcribe()`, `azure_pronunciation_assessment()`, `get_audio_recorder_component()`, `render_audio_recorder()` ... (+1)

**Key Imports:** audio_recorder_streamlit, azure, dataclasses, io, random, streamlit

---

### `grosser_baer\feedback_generator.py`
*546 Zeilen*
> Feedback-Generierung für Großer Bär.

**Klassen:**
- `FeedbackResult` → to_dict
- `FeedbackGenerator` → __init__, generate, generate_from_audio_result

**Funktionen:** `analyze_with_kleiner_baer()`, `_mock_kleiner_baer_analysis()`, `get_anthropic_client()`, `generate_narrative_with_claude()`, `generate_mock_narrative()`, `generate_feedback()`, `quick_analyze()`, `batch_generate_feedback()` ... (+3)

**Key Imports:** anthropic, audio_handler, dataclasses, disce_core, prompts

---

### `grosser_baer\prompts.py`
*261 Zeilen*
> Prompt-Architektur für Großer Bär.

**Funktionen:** `get_meta_prompt()`, `build_feedback_prompt()`, `get_phase_ui()`

---

### `grosser_baer\session_logger.py`
*565 Zeilen*
> Session-Logging für Großer Bär.

**Klassen:**
- `SessionLogger` → __init__, _get_log_dir, _ensure_log_dir, ... (+23)

**Funktionen:** `create_session_record()`, `load_session()`, `load_all_sessions()`, `export_sessions_csv()`, `get_session_summary_stats()`, `_count_tasks()`

**Key Imports:** csv, uuid

---

### `grosser_baer\task_templates.py`
*106 Zeilen*
> Berufliche Speaking-Szenarien für Großer Bär.

**Funktionen:** `get_task()`, `get_all_tasks()`, `get_tasks_by_context()`, `get_task_choices()`

---

## 📁 pages

### `pages\admin.py`
*1286 Zeilen*
> 🛠️ Admin Dashboard für Großer Bär

**Klassen:**
- `MockFeedback` → __init__

**Funktionen:** `apply_screen_state()`, `check_admin_auth()`, `render_json_with_schema()`, `get_data_hint()`, `get_all_jsons()`, `render_admin_dashboard()`

**Key Imports:** config, grosser_baer, random, streamlit, uuid

---

### `pages\grosser_baer.py`
*1363 Zeilen*
> Großer Bär – Speaking Coach UI

**Klassen:**
- `GPTFeedback` → __init__

**Funktionen:** `generate_user_code()`, `validate_user_code()`, `reset_session()`, `logout_user()`, `build_coach_input()`, `update_coach_input_with_reflection()`, `send_session_to_airtable()`

**Key Imports:** audio_recorder_streamlit, config, disce_core, grosser_baer, openai_services, random

---
