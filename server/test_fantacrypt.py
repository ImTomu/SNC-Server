# SNC-Server, an Attorney Online server
#
# Copyright (C) 2020 Hitomu
#
# Derivative of tsuserver3, an Attorney Online server. Copyright (C) 2016 argoneus <argoneuscze@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from server.fantacrypt import fanta_decrypt, fanta_encrypt

def test_fanta_decrypt():
    assert fanta_decrypt("4D90") == "MS"

def test_fanta_encrypt():
    assert fanta_encrypt("MS") == "4D90"