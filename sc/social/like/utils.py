# -*- coding:utf-8 -*-
from Acquisition import aq_base
from Products.Archetypes.interfaces import IBaseContent
from zope.annotation.interfaces import IAnnotations
from zope.globalrequest import getRequest


def get_images_view(context):
    request = getRequest()
    key = "cache-view-%s" % (context)
    cache = IAnnotations(request)
    value = cache.get(key, None)
    if not value:
        view = context.unrestrictedTraverse('@@images', None)
        field = 'image'
        if view:
            fields = ['image', 'leadImage', 'portrait']
            if IBaseContent.providedBy(context):
                schema = context.Schema()
                field = [f for f in schema.keys() if f in fields]
                if field:
                    field = field[0]
        value = (view, field) if (view and field) else (None, None)
        cache[key] = value
    return value


def get_content_image(context,
                      scale='large',
                      width=None,
                      height=None):
    request = getRequest()
    modification = context.ModificationDate()
    key = "cache-%s-%s-%s-%s-%s" % (context, modification, scale, width, height)
    cache = IAnnotations(request)
    img = cache.get(key, None)
    if not img:
        view, field = get_images_view(context)
        if view:
            try:
                sizes = view.getImageSize(field)
            except AttributeError:
                sizes = img = None
            if sizes:
                kwargs = {}
                if not (width or height):
                    kwargs['scale'] = scale
                else:
                    new = (width, height)
                    width, height = _image_size(sizes, new)
                    kwargs['width'] = width
                    kwargs['height'] = height
                    kwargs['direction'] = 'down'
                try:
                    img = view.scale(fieldname=field, **kwargs)
                except AttributeError:
                    img = None
        cache[key] = img
    return img


def get_language(context):
    ps = context.restrictedTraverse('plone_portal_state')
    default_language = ps.default_language()
    content = aq_base(context)
    if IBaseContent.providedBy(content):
        language = content.Language()
    else:
        language = content.language if hasattr(content, 'language') else ''
    return language if language else default_language


def _image_size(current, new):
    # Current width, height and aspect ratio
    c_width, c_height = current
    c_aspect = float(c_width) / float(c_height)
    # New width, height
    n_width, n_height = new

    # If new dimensions are larger than the current ones, we
    # return the current dimensions
    if (n_width > c_width) or (n_height > c_height):
        return current
    width = n_width
    height = int(round(float(width) / c_aspect))
    if n_height > height:
        height = n_height
        width = int(round(height * c_aspect))
        if n_width > width:
            return current
    return (width, height)
