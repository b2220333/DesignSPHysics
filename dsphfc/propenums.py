#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""DesignSPHysics Property enums.

This file holds a collection of useful enums
in class forms, for code organization
"""

# Copyright (C) 2016 - Andrés Vieira (anvieiravazquez@gmail.com)
# EPHYSLAB Environmental Physics Laboratory, Universidade de Vigo
#
# This file is part of DesignSPHysics.
#
# DesignSPHysics is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DesignSPHysics is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DesignSPHysics.  If not, see <http://www.gnu.org/licenses/>.


class IrregularSpectrum:
    """ Types of supported wave spectrums. """
    JONSWAP = 0
    PIERSON_MOSKOWITZ = 1

    def __init__(self):
        # Dummy init
        pass


class IrregularDiscretization:
    """ Types of supported spectrum discretization. """
    REGULAR = 0
    RANDOM = 1
    STRETCHED = 2
    COSSTRETCHED = 3

    def __init__(self):
        # Dummy init
        pass
