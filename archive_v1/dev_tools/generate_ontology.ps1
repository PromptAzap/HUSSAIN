$ErrorActionPreference = "Stop"
$folder = "."
$files = Get-ChildItem -Path $folder -Filter "*.json"

$ttl = New-Object System.Text.StringBuilder

[void]$ttl.AppendLine("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .")
[void]$ttl.AppendLine("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
[void]$ttl.AppendLine("@prefix owl: <http://www.w3.org/2002/07/owl#> .")
[void]$ttl.AppendLine("@prefix skos: <http://www.w3.org/2004/02/skos/core#> .")
[void]$ttl.AppendLine("@prefix hesin: <http://hesin.org/ontology#> .")
[void]$ttl.AppendLine("")

[void]$ttl.AppendLine("hesin:Concept a owl:Class .")
[void]$ttl.AppendLine("hesin:Lesson a owl:Class .")
[void]$ttl.AppendLine("hesin:ConceptGroup a owl:Class .")
[void]$ttl.AppendLine("hesin:Collection a owl:Class .")
[void]$ttl.AppendLine("")

function Encode-TtlString ($str) {
    if ([string]::IsNullOrEmpty($str)) { return '""@ar' }
    $s = $str -replace '\\', '\\\\'
    $s = $s -replace '"""', '\"\"\"'
    return ('"""' + $s + '"""@ar')
}

function Encode-Id ($id) {
    if ([string]::IsNullOrEmpty($id)) { return "hesin:Unknown" }
    $s = $id -replace '[^a-zA-Z0-9_]', '_'
    return "hesin:$s"
}

$fileIndex = 1

foreach ($f in $files) {
    Write-Output "Processing $($f.Name)..."
    $jsonContent = Get-Content -Path $f.FullName -Raw -Encoding UTF8
    $json = $jsonContent | ConvertFrom-Json
    $fPrefix = "F${fileIndex}_"
    
    # Collection
    $cName = $json.collection.name
    $cDesc = $json.collection.description
    $cId = Encode-Id ($fPrefix + "Collection")
    [void]$ttl.AppendLine($cId + " a hesin:Collection ;")
    [void]$ttl.AppendLine("    rdfs:label " + (Encode-TtlString $cName) + " ;")
    [void]$ttl.AppendLine("    hesin:description " + (Encode-TtlString $cDesc) + " .")
    
    # Lesson
    $lTitle = $json.lesson.title
    $lId = Encode-Id ($fPrefix + "Lesson")
    [void]$ttl.AppendLine($lId + " a hesin:Lesson ;")
    [void]$ttl.AppendLine("    rdfs:label " + (Encode-TtlString $lTitle) + " ;")
    [void]$ttl.AppendLine("    hesin:belongsToCollection " + $cId + " .")
    
    # Concept Groups
    $groups = @{}
    if ($null -ne $json.concept_groups) {
        $gIndex = 1
        foreach ($g in $json.concept_groups) {
            $gName = $g.group_name
            $gId = Encode-Id ($fPrefix + "Group_" + $gIndex)
            $groups[$gName] = $gId
            [void]$ttl.AppendLine($gId + " a hesin:ConceptGroup ;")
            [void]$ttl.AppendLine("    rdfs:label " + (Encode-TtlString $gName) + " ;")
            [void]$ttl.AppendLine("    hesin:belongsToLesson " + $lId + " .")
            $gIndex++
        }
    }
    
    # Concepts
    if ($null -ne $json.concepts) {
        foreach ($c in $json.concepts) {
            $cRawId = $c.concept_id_placeholder
            if ([string]::IsNullOrEmpty($cRawId)) { $cRawId = $c.lesson_concept_id }
            $cId = Encode-Id ($fPrefix + $cRawId)
            
            [void]$ttl.AppendLine($cId + " a hesin:Concept ;")
            [void]$ttl.AppendLine("    rdfs:label " + (Encode-TtlString $c.name) + " ;")
            [void]$ttl.AppendLine("    hesin:definition " + (Encode-TtlString $c.definition) + " ;")
            
            if ($c.importance) { [void]$ttl.AppendLine("    hesin:importance " + (Encode-TtlString $c.importance) + " ;") }
            if ($c.confidence) { [void]$ttl.AppendLine("    hesin:confidence " + (Encode-TtlString $c.confidence) + " ;") }
            if ($c.foundational_quote) { [void]$ttl.AppendLine("    hesin:foundational_quote " + (Encode-TtlString $c.foundational_quote) + " ;") }
            if ($c.actions) { [void]$ttl.AppendLine("    hesin:actions " + (Encode-TtlString $c.actions) + " ;") }
            
            if ($null -ne $c.synonyms) {
                foreach ($syn in $c.synonyms) {
                    [void]$ttl.AppendLine("    hesin:hasSynonym " + (Encode-TtlString $syn) + " ;")
                }
            }
            if ($null -ne $c.components) {
                foreach ($comp in $c.components) {
                    [void]$ttl.AppendLine("    hesin:hasComponent " + (Encode-TtlString $comp) + " ;")
                }
            }
            
            if (-not [string]::IsNullOrEmpty($c.group_name) -and $groups.ContainsKey($c.group_name)) {
                $sgId = $groups[$c.group_name]
                [void]$ttl.AppendLine("    hesin:belongsToGroup " + $sgId + " ;")
            }
            
            [void]$ttl.AppendLine("    hesin:belongsToLesson " + $lId + " .")
        }
    }
    
    # Relations
    $relMap = @{
        "يؤسس لـ" = "hesin:establishes"
        "يضاد" = "hesin:opposes"
        "يسبب" = "hesin:causes"
        "وسيلة لـ" = "hesin:isMeansFor"
        "يسبق" = "hesin:precedes"
        "شرط لـ" = "hesin:isConditionFor"
        "أعم من" = "skos:broader"
        "أخص من" = "skos:narrower"
        "ينفي" = "hesin:negates"
        "يسبب عن" = "hesin:isCausedBy"
    }
    
    if ($null -ne $json.relations) {
        foreach ($r in $json.relations) {
            $sId = Encode-Id ($fPrefix + $r.source_concept_id_placeholder)
            $tId = Encode-Id ($fPrefix + $r.target_concept_id_placeholder)
            
            $pred = "hesin:relatedTo"
            if (-not [string]::IsNullOrEmpty($r.relation_type) -and $relMap.ContainsKey($r.relation_type)) {
                $pred = $relMap[$r.relation_type]
            }
            
            [void]$ttl.AppendLine($sId + " " + $pred + " " + $tId + " .")
            if ($r.reason) {
                [void]$ttl.AppendLine("<< " + $sId + " " + $pred + " " + $tId + " >> rdfs:comment " + (Encode-TtlString $r.reason) + " .")
            }
        }
    }
    
    $fileIndex++
}

[System.IO.File]::WriteAllText("unified_ontology.ttl", $ttl.ToString(), [System.Text.Encoding]::UTF8)
Write-Output "Unified Ontology mapped and saved to unified_ontology.ttl successfully!"
