import CoreData

// No .xcdatamodeld is needed: build a minimal model in code.
let model = NSManagedObjectModel()
let entity = NSEntityDescription()
entity.name = "Note"
entity.managedObjectClassName = NSStringFromClass(NSManagedObject.self)
let title = NSAttributeDescription()
title.name = "title"
title.attributeType = .stringAttributeType
title.isOptional = false
entity.properties = [title]
model.entities = [entity]

let coordinator = NSPersistentStoreCoordinator(managedObjectModel: model)
try coordinator.addPersistentStore(ofType: NSInMemoryStoreType,
                                  configurationName: nil, at: nil)
let writer = NSManagedObjectContext(concurrencyType: .mainQueueConcurrencyType)
writer.persistentStoreCoordinator = coordinator
let reader = NSManagedObjectContext(concurrencyType: .mainQueueConcurrencyType)
reader.persistentStoreCoordinator = coordinator

let note = NSEntityDescription.insertNewObject(forEntityName: "Note", into: writer)
note.setValue("저장 시점", forKey: "title")
try writer.obtainPermanentIDs(for: [note])
precondition(!note.objectID.isTemporaryID)
let request = NSFetchRequest<NSManagedObject>(entityName: "Note")
let before = try reader.count(for: request)
try writer.save()
let after = try reader.count(for: request)
precondition(before == 0 && after == 1)
print("permanent ID before save:", !note.objectID.isTemporaryID)
print("reader count before save:", before)
print("reader count after save:", after)
