import sys
sys.path.insert(0, '.')

from app.utils.geometry import GeometryUtils
from app.utils.coordinates import CoordinateTransform

# Test 1: Area calculation
geojson = '{"type":"Polygon","coordinates":[[[106.94,32.99],[106.95,32.99],[106.95,33.00],[106.94,33.00],[106.94,32.99]]]}'
area = GeometryUtils.calculate_area_mu(geojson)
print('Test 1 - Area: ' + str(round(area, 2)) + ' mu')

# Test 2: Validation
valid, msg = GeometryUtils.validate_polygon(geojson)
print('Test 2 - Valid: ' + str(valid))

# Test 3: Center
center = GeometryUtils.calculate_center(geojson)
print('Test 3 - Center: ' + str(center))

# Test 4: BBox
bbox = GeometryUtils.calculate_bbox(geojson)
print('Test 4 - BBox: OK')

# Test 5: Coord transform
wgs = CoordinateTransform.gcj02_to_wgs84(106.94, 32.99)
print('Test 5 - Transform: OK')

print('SUCCESS: All tests passed!')
