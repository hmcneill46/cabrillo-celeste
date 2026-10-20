import SwiftUI

// Preserve newer presentation on newer systems. iOS15 uses the same content,
// actions and data with navigation and sheet APIs available on that system.
struct CJNavigation<Content: View>: View {
    let content: Content
    init(@ViewBuilder content: () -> Content) { self.content = content() }
    var body: some View {
        if #available(iOS 16, *) { NavigationStack { content } }
        else { NavigationView { content }.navigationViewStyle(.stack) }
    }
}

struct CJUnavailableView<Title: View, Detail: View, Actions: View>: View {
    let title: Title
    let detail: Detail
    let actions: Actions
    init(@ViewBuilder _ title: () -> Title, @ViewBuilder description: () -> Detail, @ViewBuilder actions: () -> Actions) {
        self.title = title(); self.detail = description(); self.actions = actions()
    }
    init(_ title: String, systemImage: String, description: Text) where Title == Label<Text, Image>, Detail == Text, Actions == EmptyView {
        self.title = Label(title, systemImage: systemImage); self.detail = description; self.actions = EmptyView()
    }
    var body: some View {
        if #available(iOS 17, *) { ContentUnavailableView { title } description: { detail } actions: { actions } }
        else {
            VStack(spacing: 14) { title.font(.headline); detail.foregroundStyle(.secondary); actions }
                .multilineTextAlignment(.center).frame(maxWidth: .infinity).padding(.vertical, 28)
        }
    }
}

struct CJResponsiveRow<Wide: View, Narrow: View>: View {
    let wide: Wide
    let narrow: Narrow
    init(@ViewBuilder wide: () -> Wide, @ViewBuilder narrow: () -> Narrow) { self.wide = wide(); self.narrow = narrow() }
    var body: some View {
        if #available(iOS 16, *) { ViewThatFits(in: .horizontal) { wide; narrow } }
        else { narrow }
    }
}

struct CJLabeledContent: View {
    let title: String
    let value: String
    init(_ title: String, value: String) { self.title = title; self.value = value }
    var body: some View {
        if #available(iOS 16, *) { LabeledContent(title, value: value) }
        else { HStack(alignment: .firstTextBaseline) { Text(title); Spacer(); Text(value).foregroundStyle(.secondary).multilineTextAlignment(.trailing) } }
    }
}

extension View {
    @ViewBuilder func cjKeyboardDismissal() -> some View {
        if #available(iOS 16, *) { scrollDismissesKeyboard(.interactively) } else { self }
    }
    @ViewBuilder func cjFilterSheet() -> some View {
        if #available(iOS 16, *) { presentationDetents([.medium, .large]).presentationDragIndicator(.visible) } else { self }
    }
    @ViewBuilder func cjHideTabBar() -> some View {
        if #available(iOS 16, *) { toolbar(.hidden, for: .tabBar) } else { self }
    }
    @ViewBuilder func cjReservedLines(_ count: Int) -> some View {
        if #available(iOS 16, *) { lineLimit(count, reservesSpace: true) } else { lineLimit(count) }
    }
}
