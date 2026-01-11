import math

class VisualEngine:
    def __init__(self, image_path, z, tile_x, tile_y):
        self.image_path = image_path
        self.z = z
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.pixels = None
        self.width = 0
        self.height = 0
        self._load_image()
        
    def _load_image(self):
        # We need to read the JPG without PIL if possible to keep dependencies low?
        # But for image processing, standard library doesn't have good support.
        # Let's hope the environment has Pillow or we use a hack (header parsing not enough).
        # Wait, the user has 'python3', likely key libraries.
        # If not, I can try to use a simple netpbm converter or just assume we have PIL.
        # Standard python env usually has Pillow.
        try:
            from PIL import Image
            with Image.open(self.image_path) as img:
                self.img = img.convert('L') # Grayscale
                self.width, self.height = self.img.size
                self.pixels = list(self.img.getdata())
                print(f"Loaded Satellite Image: {self.width}x{self.height}")
        except ImportError:
            print("PIL (Pillow) not found. Visual Topology disabled (returning 0).")
            self.pixels = None
        except Exception as e:
            print(f"Error loading image: {e}")
            self.pixels = None

    def latlon_to_pixel(self, lat, lon):
        if not self.pixels:
            return None, None
            
        n = 2.0 ** self.z
        
        # X
        x_global = (lon + 180.0) / 360.0 * n
        # Y
        rad_lat = math.radians(lat)
        y_global = (1.0 - math.log(math.tan(rad_lat) + (1.0 / math.cos(rad_lat))) / math.pi) / 2.0 * n
        
        # Local pixel coords
        # tile_x is the integer part of x_global for the tile origin
        # We need relative position within the tile.
        
        # Current tile covers [tile_x, tile_x+1)
        if int(x_global) != self.tile_x or int(y_global) != self.tile_y:
            # Point is outside this tile
            return None, None
            
        x_rel = (x_global - self.tile_x) * self.width
        y_rel = (y_global - self.tile_y) * self.height
        
        return int(x_rel), int(y_rel)

    def get_cloud_factor(self, lat, lon):
        """Returns specific cloud brightness (0.0 to 1.0).
        JMA IR TBB: Usually White (High Value) = Cold/High Cloud.
        """
        if not self.pixels:
            return 0.0
            
        x, y = self.latlon_to_pixel(lat, lon)
        if x is None:
            return 0.0 # Out of bounds
            
        # Get pixel value
        # pixels is a flat list
        idx = y * self.width + x
        if 0 <= idx < len(self.pixels):
            val = self.pixels[idx]
            # Normalize 0-255 to 0.0-1.0
            # Assuming Whiter = Stronger Cloud
            return val / 255.0
        return 0.0
