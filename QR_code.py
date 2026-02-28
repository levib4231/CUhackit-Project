import qrcode # type: ignore

# Data you want to encode
data = "http://127.0.0.1:5500/CUTRACKIT/Dashboard/index.html"

# Generate the QR code image
img = qrcode.make(data)

# Save the image to a file
img.save("my_qr_code.png")

print("QR code generated and saved as 'my_qr_code.png'")