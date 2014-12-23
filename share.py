import requests
import nacl
import nacl.utils
import nacl.secret
import binascii
from nacl.public import PrivateKey, Box
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend


def hkdf_expand(key, info, salt=None):
    backend = default_backend()
    salt = salt or os.urandom(len(key))
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=salt, info=info,
                backend=backend)
    return hkdf.derive(key), salt


email = 'tarek@ziade.org'
appname = 'someapp'
appkey = '12345'
root = 'http://localhost:8000/'
key_url = root + email + '/' + appname + '/key?appkey=' + appkey


def get_key(email, appname, appkey):
    result = requests.get(key_url)
    if result.status_code == 404:
        return None
    data = result.json()
    box = nacl.secret.SecretBox(kBr)
    nonce = binascii.unhexlify(data['nonce'])
    encPrivKey = binascii.unhexlify(data['encPrivKey'])
    encrypted_private_key = nacl.utils.EncryptedMessage(encPrivKey)
    private_key = box.decrypt(encrypted_private_key)
    private_key = PrivateKey(private_key)
    return private_key, private_key.public_key


def post_key(email, appname, pub_key, enc_priv_key, nonce, appkey):
    options = {'pubKey': pub_key, 'encPrivKey': enc_priv_key,
               'nonce': nonce}
    result = requests.post(key_url, data=options)
    if result.status_code != 200:
        raise Exception('Failed')


def generate_keys():
    # generate random private/public key
    private_key = PrivateKey.generate()
    return private_key, private_key.public_key


def encrypt_key(key, secret):
    # encrypt the private key with our secret
    box = nacl.secret.SecretBox(secret)
    nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
    encrypted = box.encrypt(key.encode(), nonce)
    encrypted = binascii.hexlify(encrypted)
    return encrypted, binascii.hexlify(nonce)


# let's sign into FxA and grab kA, kB
from fxa.core import Client
from getpass import getpass

client = Client("https://api.accounts.firefox.com")

email = raw_input('FxA email: ')
password = getpass('FxA password: ')

print('Login into FxA')
session = client.login(email, password, keys=True)
print('Fetching the keys')
kA, kB = session.fetch_keys(stretchpwd=password)

# kB key derived for our app
print('Creating kBr')
__, kBr = hkdf_expand(kB, b"SharingApp")

# let's generate a public and a private key pair
print('Generating a key/pair')
priv, pub = generate_keys()
pub = binascii.hexlify(pub.encode())
enc_priv, nonce = encrypt_key(priv, kBr)

# posting the key to the user directory service
print('Posting the Key pair to the directory')
post_key(email, appname, pub, enc_priv, nonce, appkey)

# getting the key out of the user directory service
print('Fetching the Key pair from the directory')

print(get_key(email, appname, appkey))

