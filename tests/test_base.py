import pytest

import frontend_editables


def test_unsupported_installer_strategy_assignment_raises(monkeypatch):
    monkeypatch.setattr("frontend_editables.BaseEditableInstaller.registry", [])

    class Foo(
        frontend_editables.BaseEditableInstaller,
        priority=100,
        supported_strategies=frozenset({frontend_editables.EditableStrategy.lax}),
        label="foo",
    ):
        pass

    with pytest.raises(ValueError, match="Unsupported strategy"):
        Foo("foo", "", {}, frontend_editables.EditableStrategy.strict)

    foo = Foo("foo", "", {}, frontend_editables.EditableStrategy.lax)
    with pytest.raises(ValueError, match="Unsupported strategy"):
        foo.strategy = frontend_editables.EditableStrategy.strict


@pytest.mark.parametrize("strategy", frontend_editables.EditableStrategy)
def test_installer_candidates_exhausted(monkeypatch, strategy):
    monkeypatch.setattr("frontend_editables.BaseEditableInstaller.registry", [])

    with pytest.raises(ValueError, match="No installer could satisfy strategy"):
        frontend_editables.install("foo", "", {}, strategy)


def test_adding_installer_with_duplicate_label_raises(monkeypatch):
    monkeypatch.setattr("frontend_editables.BaseEditableInstaller.registry", [])

    class Foo(
        frontend_editables.BaseEditableInstaller,
        priority=100,
        supported_strategies=frozenset({frontend_editables.EditableStrategy.lax}),
        label="foo",
    ):
        pass

    with pytest.raises(ValueError, match="Labels must be unique"):

        class Bar(
            frontend_editables.BaseEditableInstaller,
            priority=200,
            supported_strategies=frozenset({frontend_editables.EditableStrategy.lax}),
            label="foo",
        ):
            pass
