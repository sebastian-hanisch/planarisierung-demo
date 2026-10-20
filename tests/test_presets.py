"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Grenzen."""

import pytest

import pln_constants as C
import pln_evaluation as ev
import pln_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_regler_bounds():
    for name, p in C.PRESETS.items():
        assert p["vehicle"] in C.VEHICLES and p["classic"] in C.CLASSIC_NAMES and p["skeleton"] in C.SKELETONS and p["embedding"] in C.EMBEDDINGS, name
        assert C.N_MIN <= p["n"] <= C.N_MAX and C.EXTRAS_MIN <= p["extras"] <= C.EXTRAS_MAX and C.TRIES_MIN <= p["tries"] <= C.TRIES_MAX and 0 <= p["seed"] <= C.SEED_MAX, name


def test_default_preset_equals_the_default_settings_and_is_first():
    assert ev.Settings(**C.PRESETS[next(iter(C.PRESETS))]) == ev.Settings()


def test_presets_differ_from_each_other():
    values = [tuple(sorted(p.items())) for p in C.PRESETS.values()]
    assert len(set(values)) == len(values)


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_setting_defaults_equal_the_constants():
    assert {k: s.default for k, s in P.SETTING_SPECS.items()} == {
        "vehicle_select": C.DEFAULT_VEHICLE, "n_slider": C.DEFAULT_N, "extras_slider": C.DEFAULT_EXTRAS, "classic_select": C.DEFAULT_CLASSIC, "skeleton_select": C.DEFAULT_SKELETON,
        "embedding_select": C.DEFAULT_EMBEDDING, "tries_slider": C.DEFAULT_TRIES, "seed_input": C.DEFAULT_SEED}


@pytest.mark.parametrize("key,raw,expected", [
    ("n_slider", "150", 150), ("n_slider", "3", C.N_MIN), ("n_slider", "9999", C.N_MAX), ("n_slider", "abc", None), ("extras_slider", ["7"], 7),
    ("extras_slider", "-2", C.EXTRAS_MIN), ("extras_slider", "99", C.EXTRAS_MAX), ("tries_slider", "0", C.TRIES_MIN), ("tries_slider", "99", C.TRIES_MAX), ("seed_input", "9999999", C.SEED_MAX),
    ("vehicle_select", "classic", "classic"), ("vehicle_select", "ring", None), ("skeleton_select", "cover", "cover"), ("skeleton_select", "x", None),
    ("embedding_select", "arbitrary", "arbitrary"), ("classic_select", "K5", "K5"), ("classic_select", "K9", None),
])
def test_permalink_values_are_clamped_or_rejected(key, raw, expected):
    assert P._coerce(P.SETTING_SPECS[key], raw) == expected


def test_url_parameters_are_distinct():
    params = [s.url_param for s in P.SETTING_SPECS.values()]
    assert len(set(params)) == len(params)


def test_bounds_of_choice_settings_are_first_and_last_option():
    assert P.bounds("vehicle_select") == ("delaunay", "classic") and P.bounds("skeleton_select") == ("length", "cover") and P.bounds("embedding_select") == ("geometry", "arbitrary")
    assert P.bounds("n_slider") == (C.N_MIN, C.N_MAX) and P.bounds("tries_slider") == (C.TRIES_MIN, C.TRIES_MAX) and P.bounds("classic_select") == ("K5", "Petersen")
