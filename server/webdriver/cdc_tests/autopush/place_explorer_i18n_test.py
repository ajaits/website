# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import unittest

from server.webdriver.cdc_tests.autopush.cdc_base_webdriver import \
    CdcAutopushTestBase
from server.webdriver.cdc_tests.autopush.cdc_base_webdriver import \
    SKIPPED_TEST_REASON
from server.webdriver.shared_tests.place_explorer_i18n_test import \
    PlaceI18nExplorerTestMixin


class TestPlaceExplorerI18n(PlaceI18nExplorerTestMixin, CdcAutopushTestBase):
  """Class to test the i18n place explorer page for Custom DC. Tests come from PlaceI18nExplorerTestMixin."""

  @unittest.skip(reason=SKIPPED_TEST_REASON)
  def test_explorer_redirect_place_explorer_keeps_locale(self):
    super().test_explorer_redirect_place_explorer_keeps_locale()
