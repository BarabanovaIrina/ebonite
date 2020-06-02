from typing import Tuple

import pyjackson as pj
from flask import Blueprint, Response, jsonify, request
from pyjackson.pydantic_ext import PyjacksonModel

from ebonite.api.helpers import ModelIdValidator
from ebonite.client.base import Ebonite
from ebonite.core.errors import ExistingImageError, ImageWithInstancesError, NonExistingImageError
from ebonite.core.objects import Image


class BuildImageBody(PyjacksonModel):
    __type__ = Image
    __include__ = ['name', 'model_id']
    __force_required__ = ['model_id']


class UpdateImageBody(PyjacksonModel):
    __type__ = Image
    __include__ = ['id', 'name', 'model_id']
    __force_required__ = ['id', 'model_id']


def images_blueprint(ebonite: Ebonite) -> Blueprint:
    blueprint = Blueprint('images', __name__, url_prefix='/images')

    @blueprint.route('', methods=['GET'])
    def get_images() -> Tuple[Response, int]:
        model_id = request.args.get('model_id')
        ModelIdValidator(model_id=model_id)
        model = ebonite.meta_repo.get_model_by_id(model_id)
        if model is not None:
            return jsonify([ebonite.meta_repo.get_image_by_id(x) for x in model.images]), 200
        else:
            return jsonify({'errormsg': f'Model with id {model_id} does not exist'})

    @blueprint.route('/<int:id>', methods=['GET'])
    def get_image(id: int) -> Tuple[Response, int]:
        image = ebonite.meta_repo.get_image_by_id(id)
        if image is not None:
            return jsonify(pj.dumps(image)), 200
        else:
            return jsonify({'errormsg': f'Image with id {id} does not exist'})

    @blueprint.route('', methods=['POST'])
    def build_image():
        image = BuildImageBody.from_data(request.get_json(force=True))
        model = ebonite.meta_repo.get_model_by_id(image.model_id)
        if model is None:
            return jsonify({'errormsg': f'Model with id {image.model_id} does not exist'}), 404
        try:
            image = ebonite.build_image(name=image.name, model=model)
            return jsonify(pj.dumps(image)), 201
        except ExistingImageError:
            return jsonify({'errormsg': f'Image with name {image.name} already exists'}), 400

    @blueprint.route('/<int:id>', methods=['PATCH'])
    def update_image(id: int):
        body = request.get_json(force=True)
        body['id'] = id
        image = UpdateImageBody.from_data(body)
        try:
            ebonite.meta_repo.update_image(image)
            return jsonify({}), 204
        except NonExistingImageError:
            return jsonify({'errormsg': f'Project with id {id} does not exist'}), 404

    @blueprint.route('/<int:id>', methods=['DELETE'])
    def delete_image(id: int):
        cascade = False if not request.args.get('cascade') else bool(int(request.args.get('cascade')))
        image = ebonite.meta_repo.get_image_by_id(id)
        if image is None:
            return jsonify({'errormsg': f'Image with id {id} does not exist'}), 404
        try:
            ebonite.delete_image(image, cascade=cascade)
            return jsonify({}), 204
        except ImageWithInstancesError as e:
            return jsonify({'errormsg': str(e)}), 400

    return blueprint