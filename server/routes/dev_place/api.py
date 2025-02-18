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
"""
Defines endpoints for the place page.
"""

from flask import Blueprint
from flask import g
from flask import jsonify
from flask import request

from server.lib.cache import cache
from server.lib.util import error_response
from server.lib.util import log_execution_time
from server.routes import TIMEOUT
from server.routes.dev_place import utils as place_utils
from server.routes.dev_place.types import PlaceChartsApiResponse
from server.routes.dev_place.types import RelatedPlacesApiResponse

OVERVIEW_CATEGORY = "Overview"
CATEGORIES = {
    OVERVIEW_CATEGORY, "Economics", "Health", "Equity", "Crime", "Education",
    "Demographics", "Housing", "Environment", "Energy"
}

# Define blueprint
bp = Blueprint("dev_place_api", __name__, url_prefix='/api/dev-place')


@bp.route('/charts/<path:place_dcid>')
@log_execution_time
@cache.cached(timeout=TIMEOUT, query_string=True)
def place_charts(place_dcid: str):
  """
  Returns chart definitions for the specified place based on the availability of
  of data for that place. Results are translated into the user's locale.

  Args:
      place_dcid (str): DCID of the place to fetch data for.

  Returns:
      Response: JSON-encoded PlaceChartsApiResponse object
  
  The response includes:
  - Place details (name, type, etc.)
  - Charts specific to the place
  - Translated category strings for the charts
  """
  # Ensure category is valid
  place_category = request.args.get("category", OVERVIEW_CATEGORY)
  parent_place_dcid = place_utils.get_place_override(
      place_utils.get_parent_places(place_dcid))
  if place_category not in CATEGORIES:
    return error_response(
        f"Argument 'category' {place_category} must be one of: {', '.join(CATEGORIES)}"
    )

  # Fetch place info
  place = place_utils.fetch_place(place_dcid, locale=g.locale)

  # Determine child place type
  ordered_child_place_types = place_utils.get_child_place_types(place)
  child_place_type = ordered_child_place_types[
      0] if ordered_child_place_types else None

  # Retrieve available place page charts
  full_chart_config = place_utils.read_chart_configs()

  chart_config_for_category = place_utils.filter_chart_configs_for_category(
      place_category, full_chart_config)

  # Filter out place page charts that don't have any data for the current place_dcid
  filtered_chart_config = place_utils.filter_chart_config_by_place_dcid(
      chart_config=chart_config_for_category,
      place_dcid=place_dcid,
      place_type=place_utils.place_type_to_highlight(place.types),
      child_place_type=child_place_type,
      parent_place_dcid=parent_place_dcid)

  # TODO(gmechali): Right now we're duplicating some of this. We should always only execute the call on the full chart config, THEN do the filtering by category.
  # Always execute the full chart config to fetch all categories with data.
  filtered_chart_config_for_category = (
      place_utils.filter_chart_config_by_place_dcid(
          chart_config=full_chart_config,
          place_dcid=place_dcid,
          place_type=place_utils.place_type_to_highlight(place.types),
          child_place_type=child_place_type,
          parent_place_dcid=parent_place_dcid))

  # Translate chart config titles
  translated_chart_config = place_utils.translate_chart_config(
      filtered_chart_config)

  # Extract charts to Chart objects used in PlaceChartsApiResponse object
  blocks = place_utils.chart_config_to_overview_charts(translated_chart_config,
                                                       child_place_type)

  # Translate category strings
  translated_category_strings = place_utils.get_translated_category_strings(
      filtered_chart_config_for_category)

  response = PlaceChartsApiResponse(
      blocks=blocks,
      place=place,
      translatedCategoryStrings=translated_category_strings)
  return jsonify(response)


@bp.route('/related-places/<path:place_dcid>')
@log_execution_time
@cache.cached(timeout=TIMEOUT, query_string=True)
def related_places(place_dcid: str):
  """
  Fetches and returns related place data to the specified place.
  Results are translated into the user's locale.

  Args:
      place_dcid (str): DCID of the place to fetch data for.

  Returns:
      Response: JSON-encoded RelatedPlacesApiResponse object
  
  The response includes:
  - Place details (name, type, etc.)
  - Lists of nearby, similar, and child places
  """
  # Fetch place info
  place = place_utils.fetch_place(place_dcid, locale=g.locale)

  # Fetch nearby, similar, and child place dcids
  nearby_place_dcids = place_utils.fetch_nearby_place_dcids(place,
                                                            locale=g.locale)
  similar_place_dcids = place_utils.fetch_similar_place_dcids(place,
                                                              locale=g.locale)
  ordered_child_place_types = place_utils.get_child_place_types(place)
  primary_child_place_type = ordered_child_place_types[
      0] if ordered_child_place_types else None

  child_place_dcids = []
  seen_dcids = set(
  )  # Keep track of seen DCIDs to prevent dupes but keep ordering.

  # TODO(gmechali): Refactor this into async calls.
  for child_place_type in ordered_child_place_types:
    for dcid in place_utils.fetch_child_place_dcids(place,
                                                    child_place_type,
                                                    locale=g.locale):
      if dcid not in seen_dcids:
        child_place_dcids.append(dcid)
        seen_dcids.add(dcid)

  parent_places = place_utils.get_parent_places(place.dcid)

  # Fetch all place objects in one request to reduce latency (includes name and typeOf)
  all_place_dcids = [
      place_dcid, *nearby_place_dcids, *similar_place_dcids, *child_place_dcids
  ]
  all_places = place_utils.fetch_places(all_place_dcids, locale=g.locale)

  # Get place objects for nearby, similar, and child places
  all_place_by_dcid = {p.dcid: p for p in all_places}
  nearby_places = [
      all_place_by_dcid[dcid]
      for dcid in nearby_place_dcids
      if not all_place_by_dcid[dcid].dissolved
  ]
  similar_places = [
      all_place_by_dcid[dcid]
      for dcid in similar_place_dcids
      if not all_place_by_dcid[dcid].dissolved
  ]
  child_places = [
      all_place_by_dcid[dcid]
      for dcid in child_place_dcids
      if not all_place_by_dcid[dcid].dissolved
  ]

  response = RelatedPlacesApiResponse(childPlaceType=primary_child_place_type,
                                      childPlaces=child_places,
                                      nearbyPlaces=nearby_places,
                                      place=place,
                                      similarPlaces=similar_places,
                                      parentPlaces=parent_places)
  return jsonify(response)
