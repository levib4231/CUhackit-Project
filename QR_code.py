import qrcode # type: ignore

# Data you want to encode
data = "https://gemini.google.com/app/760c6c6a51d39343"

# Generate the QR code image
img = qrcode.make(data)

# Save the image to a file
img.save("my_qr_code.png")

print("QR code generated and saved as 'my_qr_code.png'")