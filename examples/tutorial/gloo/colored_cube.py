# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2014, Vispy Development Team. All Rights Reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
# Author: Nicolas P .Rougier
# Date:   04/03/2014
# -----------------------------------------------------------------------------

import numpy as np

from vispy import app, gloo
from vispy.gloo import Program, VertexBuffer, IndexBuffer
from vispy.util.transforms import perspective, translate, rotate
from vispy.geometry import create_cube


vertex = """
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
attribute vec3 position;
attribute vec4 color;
varying vec4 v_color;
void main()
{
    v_color = color;
    gl_Position = projection * view * model * vec4(position,1.0);
}
"""

fragment = """
varying vec4 v_color;
void main()
{
    gl_FragColor = v_color;
}
"""


class Canvas(app.Canvas):
    def __init__(self):
        app.Canvas.__init__(self, size=(512, 512), title='Colored cube',
                            keys='interactive')
        self.timer = app.Timer('auto', self.on_timer)

    def on_initialize(self, event):
        # Build cube data
        V, I, _ = create_cube()
        vertices = VertexBuffer(V)
        self.indices = IndexBuffer(I)

        # Build program
        self.program = Program(vertex, fragment)
        self.program.bind(vertices)

        # Build view, model, projection & normal
        view = translate((0, 0, -5))
        model = np.eye(4, dtype=np.float32)
        self.program['model'] = model
        self.program['view'] = view
        self.phi, self.theta = 0, 0
        gloo.set_state(clear_color=(0.30, 0.30, 0.35, 1.00), depth_test=True)
        self.timer.start()

    def on_draw(self, event):
        gloo.clear(color=True, depth=True)
        self.program.draw('triangles', self.indices)

    def on_resize(self, event):
        gloo.set_viewport(0, 0, *event.size)
        projection = perspective(45.0, event.size[0] / float(event.size[1]),
                                 2.0, 10.0)
        self.program['projection'] = projection

    def on_timer(self, event):
        self.theta += .02
        self.phi += .02
        model = rotate(self.phi, (0, 1, 0)) * rotate(self.theta, (0, 0, 1))
        self.program['model'] = model
        self.update()

if __name__ == '__main__':
    c = Canvas()
    c.show()
    app.run()
