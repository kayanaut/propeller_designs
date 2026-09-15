"""Rebuild all derived deliverables. Intentionally does NOT generate slicer or machine files."""
import pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1]
for script in ['motor_step.py','build.py','hardware.py','inspect_export.py','verify.py','check_mesh_intersections.py','check_hardware_stack.py']:
 print('RUN',script,flush=True)
 with (root/'reports'/(script.replace('.py','')+'.log')).open('w') as log:
  subprocess.run([sys.executable,str(root/'source'/script)],stdout=log,stderr=subprocess.STDOUT,check=True)
print('Finished. Review reports; unresolved gates do not become approvals.')
