from . import python

def qualify(project_root_dir): # pragma: no cover -- TODO
	""" Returns list of project type modules that given root dir qualifies for. """
	project_types = []
	if python.qualify(project_root_dir):
		project_types.append(python)
	return project_types
