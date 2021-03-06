from typing import Any, Dict

from ebonite.core.objects.core import Model


def create_model(model_object, input_data, model_name: str = None, params: Dict[str, Any] = None,
                 description: str = None, **kwargs) -> Model:
    """
    Creates Model instance from arbitrary model objects and sample of input data

    :param model_object: model object (function, sklearn model, tensorflow output tensor list etc)
    :param input_data: sample of input data (numpy array, pandas dataframe, feed dict etc)
    :param model_name: name for model in database, if not provided will be autogenerated
    :param params: dict with arbitrary parameters. Must be json-serializable
    :param description: text description of this model
    :param kwargs: other arguments for model (see Model.create)
    :return: :class:`~ebonite.core.objects.core.Model` instance
    """
    return Model.create(model_object, input_data, model_name, params, description, **kwargs)
