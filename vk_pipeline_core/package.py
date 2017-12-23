name = "vk_pipeline_core"

version = "1.0.0"

authors = [
    "Venu Krishnamurthy"
]

description = \
    """
    Testing rez build
    """

tools = [
    "test"
]

requires = [
    "python-2.7+<3"
]

uuid = "test.vk_pipeline_core_py"

def commands():
    env.PYTHONPATH.append("{root}/python")
    env.PATH.append("{root}/bin")