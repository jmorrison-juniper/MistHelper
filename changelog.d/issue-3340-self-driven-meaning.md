### Read both self-drive signals of a Marvis Action (menu 270)

- **Fixed**: The Marvis Actions API report no longer states that `self_driven`
  proves a fix by Marvis. No Mist document defines the field. In the lab
  organization, 8 rows hold `self_driven` as `True`, and the only row with the
  status `marvis_self_driven` holds no `self_driven` value. The report now tells
  the operator to read both signals, and it records a live read of the org
  setting `marvis.auto_operations` and its audit log. The comments in
  `src/marvis/actions/model.py` agree with the report. Issue #3340.
