using Mono.Cecil;
using Mono.Cecil.Cil;
using System.Text.Json;

namespace Cabrillo.Preparation;

// Applied only to the hash-verified Steam 1.4.0.0 original, before Everest.
// Equivalent offline services to the non-Steam edition; gameplay IL is retained.
internal static class SteamInputPatch
{
    internal static void Apply(string input, string output, string receipt)
    {
        using var module = ModuleDefinition.ReadModule(input);
        MethodDefinition Method(string type, string name) => module.GetType(type).Methods.Single(m => m.Name == name);
        var edits = new List<string>();
        void Empty(string type, string name, bool zero = false, bool wide = false)
        {
            var method = Method(type, name);
            method.Body = new MethodBody(method);
            if (zero) method.Body.Instructions.Add(Instruction.Create(OpCodes.Ldc_I4_0));
            if (wide) method.Body.Instructions.Add(Instruction.Create(OpCodes.Conv_I8));
            method.Body.Instructions.Add(Instruction.Create(OpCodes.Ret));
            edits.Add(method.FullName);
        }
        Empty("Celeste.Achievements", "Has", true);
        var register = Method("Celeste.Achievements", "Register");
        register.Body = new MethodBody(register);
        register.Body.Instructions.Add(Instruction.Create(OpCodes.Ldarg_0));
        register.Body.Instructions.Add(Instruction.Create(OpCodes.Call, Method("Celeste.Achievements", "Has")));
        register.Body.Instructions.Add(Instruction.Create(OpCodes.Pop));
        register.Body.Instructions.Add(Instruction.Create(OpCodes.Ret));
        edits.Add(register.FullName);
        foreach (string name in new[] { "MakeRequest", "Increment", "Store" }) Empty("Celeste.Stats", name);
        Empty("Celeste.Stats", "Has", true);
        Empty("Celeste.Stats", "Local", true);
        Empty("Celeste.Stats", "Global", true, true);

        static void Nop(Instruction instruction) { instruction.OpCode = OpCodes.Nop; instruction.Operand = null; }
        var update = Method("Celeste.Celeste", "Update");
        var callback = update.Body.Instructions.Single(i => i.Operand is MethodReference call &&
            call.FullName == "System.Void Steamworks.SteamAPI::RunCallbacks()");
        if (callback != update.Body.Instructions[0]) throw new InvalidDataException("Unexpected Steam callback site.");
        Nop(callback); edits.Add("Remove desktop Steam callback from Update");

        var main = Method("Celeste.Celeste", "Main");
        var instructions = main.Body.Instructions;
        var restart = instructions.Single(i => i.Operand is MethodReference call &&
            call.FullName == "System.Boolean Steamworks.SteamAPI::RestartAppIfNecessary(Steamworks.AppId_t)");
        int start = instructions.IndexOf(restart) - 1;
        int language = instructions.IndexOf(instructions.Single(i => i.Operand is MethodReference call &&
            call.FullName == "System.String Steamworks.SteamApps::GetCurrentGameLanguage()"));
        if (instructions[start].OpCode != OpCodes.Ldsfld || instructions[start].Operand is not FieldReference field ||
            field.FullName != "Steamworks.AppId_t Celeste.Celeste::SteamID" ||
            instructions[language + 1].OpCode != OpCodes.Stfld ||
            instructions[language + 1].Operand is not FieldReference setting || setting.FullName != "System.String Celeste.Settings::Language")
            throw new InvalidDataException("Unexpected Steam startup block.");
        // Nops preserve branch/exception targets and the desktop entry point's other logic.
        for (int i = start; i <= language + 1; i++) Nop(instructions[i]);
        edits.Add("Remove Steam client startup and client-selected language");

        var cctor = Method("Celeste.Celeste", ".cctor");
        var store = cctor.Body.Instructions.Single(i => i.OpCode == OpCodes.Stsfld &&
            i.Operand is FieldReference f && f.FullName == "Steamworks.AppId_t Celeste.Celeste::SteamID");
        if (store.Previous?.OpCode != OpCodes.Newobj || store.Previous.Operand is not MethodReference constructor ||
            constructor.FullName != "System.Void Steamworks.AppId_t::.ctor(System.UInt32)" ||
            store.Previous.Previous?.OpCode != OpCodes.Ldc_I4 || (int)store.Previous.Previous.Operand != 504230)
            throw new InvalidDataException("Unexpected Steam app identity initializer.");
        Nop(store.Previous.Previous); Nop(store.Previous); Nop(store);
        var celeste = module.GetType("Celeste.Celeste");
        celeste.Fields.Remove(celeste.Fields.Single(f => f.Name == "SteamID"));
        edits.Add("Remove desktop Steam app identity");
        var steam = module.AssemblyReferences.Single(a => a.Name == "Steamworks.NET");
        module.AssemblyReferences.Remove(steam);
        // Everest now deliberately selects its NoLauncher / non-Steam patch rules.
        module.Write(output);
        using var written = ModuleDefinition.ReadModule(output);
        if (written.AssemblyReferences.Any(a => a.Name.Contains("Steamworks", StringComparison.Ordinal)) ||
            written.GetTypeReferences().Any(t => t.Namespace == "Steamworks") ||
            written.GetMemberReferences().Any(m => m.DeclaringType.Namespace == "Steamworks"))
            throw new InvalidDataException("Desktop Steam dependencies survived the input adaptation.");
        File.WriteAllText(receipt, JsonSerializer.Serialize(new {
            status = "PASS_STEAM_INPUT_OFFLINE_SERVICES", edits, original_retained = true,
            steam_achievements_and_cloud = false, physical_device_tested = false
        }));
    }
}
