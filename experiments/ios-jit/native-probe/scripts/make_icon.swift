import AppKit

// Original geometric icon, drawn locally; no Celeste assets are distributed.
let output = URL(fileURLWithPath: CommandLine.arguments[1])
let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: 1024, pixelsHigh: 1024,
    bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
    colorSpaceName: .deviceRGB, bytesPerRow: 4096, bitsPerPixel: 32)!
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: bitmap)
NSColor(calibratedRed: 0.055, green: 0.063, blue: 0.09, alpha: 1).setFill()
NSRect(x: 0, y: 0, width: 1024, height: 1024).fill()
let mountain = NSBezierPath()
mountain.move(to: NSPoint(x: 150, y: 260))
mountain.line(to: NSPoint(x: 490, y: 785))
mountain.line(to: NSPoint(x: 870, y: 260))
mountain.close()
NSColor(calibratedRed: 0.28, green: 0.35, blue: 0.49, alpha: 1).setFill()
mountain.fill()
let ridge = NSBezierPath()
ridge.move(to: NSPoint(x: 490, y: 785))
ridge.line(to: NSPoint(x: 365, y: 592))
ridge.line(to: NSPoint(x: 483, y: 627))
ridge.line(to: NSPoint(x: 605, y: 626))
ridge.close()
NSColor(calibratedWhite: 0.95, alpha: 1).setFill(); ridge.fill()
NSColor(calibratedRed: 0.92, green: 0.28, blue: 0.4, alpha: 1).setFill()
NSBezierPath(roundedRect: NSRect(x: 347, y: 126, width: 330, height: 126), xRadius: 35, yRadius: 35).fill()
let label = "JIT" as NSString
let attributes: [NSAttributedString.Key: Any] = [.font: NSFont.monospacedSystemFont(ofSize: 88, weight: .bold), .foregroundColor: NSColor.white]
let size = label.size(withAttributes: attributes)
label.draw(at: NSPoint(x: (1024 - size.width) / 2, y: 137), withAttributes: attributes)
NSGraphicsContext.restoreGraphicsState()
try bitmap.representation(using: .png, properties: [:])!.write(to: output)
