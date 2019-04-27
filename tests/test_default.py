def test_imports():
  '''test that major imports work'''
  from vtkAtamai import (ActorFactory, ImagePane, ImagePlaneFactory, OrthoPlanesFactory,
                        PaneFrame, RenderPane, RenderPane2D, WindowLevelLabel)

def callback(evt, values):
  print("vtkAtamai Modified event callback called")

def test_actor_factory():
  from vtkAtamai import ActorFactory

  o = ActorFactory.ActorFactory()
  o.AddObserver("ModifiedEvent", callback)
  o.InvokeEvent('ModifiedEvent')
  o.tearDown()

def test_image_pane():
  from vtkAtamai import ImagePane
  pane = ImagePane.ImagePane()

def test_plane_outline_factory():
  ''' is no longer used it seems'''
  from vtkAtamai import PlaneOutlineFactory
  o = PlaneOutlineFactory.PlaneOutlineFactory()