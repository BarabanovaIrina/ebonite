from typing import Tuple

import pyjackson as pj
from flask import Blueprint, Response, jsonify, request
from pyjackson.pydantic_ext import PyjacksonModel

from ebonite.api.helpers import TaskIdValidator
from ebonite.client.base import Ebonite
from ebonite.core.errors import ModelWithImagesError, NonExistingModelError
from ebonite.core.objects.core import Model


class UpdateModelBody(PyjacksonModel):
    __type__ = Model
    __include__ = ['id', 'name', 'task_id']
    __force_required__ = ['id', 'task_id']


def models_blueprint(ebonite: Ebonite) -> Blueprint:
    blueprint = Blueprint('models', __name__, url_prefix='/models')

    @blueprint.route('', methods=['GET'])
    def get_models() -> Tuple[Response, int]:
        task_id = request.args.get('task_id')
        TaskIdValidator(task_id=task_id)
        task = ebonite.meta_repo.get_task_by_id(task_id)
        if task is not None:
            return jsonify([pj.dumps(ebonite.meta_repo.get_model_by_id(x)) for x in task.models]), 200
        else:
            return jsonify({'errormsg': f'Task with id {task_id} does not exist'}), 404

    @blueprint.route('/<int:id>', methods=['GET'])
    def get_model(id: int) -> Tuple[Response, int]:
        model = ebonite.meta_repo.get_model_by_id(id)
        if model is not None:
            return jsonify(pj.dumps(model)), 200
        else:
            return jsonify({'errormsg': f'Model with id {id} does not exist'}), 404

    @blueprint.route('/<int:id>/artifacts/<string:name>', methods=['GET'])
    def get_model_artifacts(id: int, name: str):
        model = ebonite.meta_repo.get_model_by_id(id)
        if model is None:
            return jsonify({'errormsg': f'Model with id {id} does not exist'}), 404
        artifacts = ebonite.artifact_repo.get_artifact(model)
        with artifacts.blob_dict() as blobs:
            artifact = blobs.get(name)
        if artifact is not None:
            return jsonify(pj.dumps(artifact)), 200
        else:
            return jsonify({'errormsg': f'Artifact with name {name} does not exist'}), 404

    @blueprint.route('/<int:id>', methods=['PATCH'])
    def update_model(id: int):
        body = request.get_json(force=True)
        body['id'] = id
        model = UpdateModelBody.from_data(body)
        try:
            ebonite.meta_repo.update_model(model)
            return jsonify({}), 204
        except NonExistingModelError:
            return jsonify({'errormsg': f'Model with id {id} and task_id {model.task_id} does not exist'}), 404

    @blueprint.route('/<int:id>', methods=['DELETE'])
    def delete_model(id: int):
        cascade = False if not request.args.get('cascade') else bool(int(request.args.get('cascade')))
        model = ebonite.meta_repo.get_model_by_id(id)
        if model is None:
            return jsonify({'errormsg': f'Model with id {id} does not exist'}), 404
        try:
            ebonite.delete_model(model, cascade=cascade)
            return jsonify({}), 204
        except ModelWithImagesError as e:
            return jsonify({'errormsg': str(e)}), 400

    return blueprint