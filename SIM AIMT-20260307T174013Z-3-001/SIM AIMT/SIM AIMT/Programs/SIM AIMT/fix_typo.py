# Fix the typo in app.py
with open('app.py', 'r') as f:
    content = f.read()

# Fix the typo
old = "@role_required('HOD', 'Director', 'DeanRegistrar', '', 'Faculty', 'Management')\ndef subject_attendance():"
new = "@role_required('HOD', 'Director', 'Dean', 'Registrar', 'Faculty', 'Management')\ndef subject_attendance():"

content = content.replace(old, new)

with open('app.py', 'w') as f:
    f.write(content)

print('Fixed!')
