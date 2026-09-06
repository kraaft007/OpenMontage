"""Local extensions to OpenMontage, kept out of the upstream tree.

Nothing here is imported by upstream code. The registry loads it with a second
call, `registry.discover("om_ext")`, using the package_name argument that
`ToolRegistry.discover` already accepts — so no upstream file is modified and a
`git merge upstream/main` can never conflict with anything in this directory.
"""
