__path__ = __import__('pkgutil').extend_path(__path__, __name__)


from tendril.db.models.content import ContentModel


def _get_content_models():
    return {k: v.class_ for k, v in ContentModel.__mapper__.polymorphic_map.items()}


content_models = _get_content_models()


def _get_content_types():
    return set(content_models.keys())


content_types = _get_content_types()
