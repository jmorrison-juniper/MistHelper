"""The phase watch of one multi-site upgrade (issue #3245).

The package reuses the single-site settle gate for each cascade phase. It sends
no firmware write. It reads the cloud, and it writes the operation record only.
"""
