import os
from datetime import datetime, timezone, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# generate private key and certificate
def generate_key_pair(email, name):
    # generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # subject is who does the certificate belongs to
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, name),
        x509.NameAttribute(NameOID.EMAIL_ADDRESS, email)
    ])

    # create the certificate
    cert = (
        x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(private_key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc)+ timedelta(days=365))
        .sign(private_key, hashes.SHA256())
    )

    # create files for the private key and certificate
    key_path = os.path.join("data/certs", f"{email}.key")
    cert_path = os.path.join("data/certs", f"{email}.pem")

    # write the private key
    with open(key_path, "wb") as file:
        file.write(private_key.private_bytes(
              serialization.Encoding.PEM,
              serialization.PrivateFormat.TraditionalOpenSSL,
              serialization.NoEncryption()
          ))

    # write the certificate
    with open(cert_path, "wb") as file:
        file.write(cert.public_bytes(serialization.Encoding.PEM))

    return key_path, cert_path