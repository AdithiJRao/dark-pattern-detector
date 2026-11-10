from PIL import Image, ImageDraw

for size in (48, 128):
    img = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    d = ImageDraw.Draw(img)
    w = max(4, size // 10)
    d.rectangle([w, w, size - w, size - w], outline=(216, 38, 28, 255), width=w)
    img.save(f"extension/icon{size}.png")
print("icons saved")