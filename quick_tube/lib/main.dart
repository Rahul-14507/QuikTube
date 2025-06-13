import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await Supabase.initialize(
    url: 'https://dtifhybifqbaogvsxfxo.supabase.co',
    anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR0aWZoeWJpZnFiYW9ndnN4ZnhvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgxNTE4NDcsImV4cCI6MjA2MzcyNzg0N30._UILK9VxQ00_627vY3NpCgra0ZhvjM5MM3dhOyNlVSw',
  );

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'YouTube Summarizer',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: const SummarizerScreen(),
    );
  }
}

class SummarizerScreen extends StatefulWidget {
  const SummarizerScreen({super.key});

  @override
  State<SummarizerScreen> createState() => _SummarizerScreenState();
}

class _SummarizerScreenState extends State<SummarizerScreen> {
  final TextEditingController _urlController = TextEditingController();
  String _summary = "Enter a YouTube URL to get a summary!";
  bool _isLoading = false;

  // Define your backend URL here. IMPORTANT: Choose the correct one!
  // If using Android Emulator: const String _backendUrl = 'http://10.0.2.2:5000/summarize';
  // If using Physical Android Device (and your computer is on same Wi-Fi):
  final String _backendUrl = 'http://192.168.114.219:5000/summarize'; // USE YOUR ACTUAL IP!

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  void _summarizeVideo() async {
    final String youtubeUrl = _urlController.text.trim();

    if (youtubeUrl.isEmpty) {
      setState(() {
        _summary = "Please enter a YouTube URL.";
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _summary = "Fetching and summarizing video...";
    });

    String fetchedTitle = "Unknown Title";
    String fetchedSummary = "Failed to get summary.";
    final supabase = Supabase.instance.client;

    try {
      final response = await http.post(
        Uri.parse(_backendUrl),
        headers: <String, String>{
          'Content-Type': 'application/json; charset=UTF-8',
        },
        body: jsonEncode(<String, String>{
          'url': youtubeUrl,
        }),
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> responseData = jsonDecode(response.body);
        fetchedSummary = responseData['summary'];
        fetchedTitle = responseData['video_title'] ?? "Unknown Title";

        try {
          await supabase.from('summaries').insert({
            'youtube_url': youtubeUrl,
            'video_title': fetchedTitle,
            'summary_text': fetchedSummary,
            'user_id': null,
          });
          print('Summary and Title saved to Supabase!');
        } catch (supabaseError) {
          print('Error saving summary to Supabase: $supabaseError');
        }
      } else {
        final Map<String, dynamic> errorData = jsonDecode(response.body);
        fetchedSummary = "Error from backend: ${errorData['error'] ?? 'Unknown error'}";
        fetchedTitle = "Error";
        print('Backend Error: ${response.statusCode}, ${response.body}');
      }
    } catch (e) {
      fetchedSummary = "Network or server error: $e";
      fetchedTitle = "Error";
      print('Client-side HTTP Error: $e');
    } finally {
      setState(() {
        _summary = fetchedSummary;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('YouTube Summarizer'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _urlController,
              decoration: const InputDecoration(
                labelText: 'YouTube Video URL',
                hintText: 'e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.url,
              textInputAction: TextInputAction.done,
              onSubmitted: (_) => _summarizeVideo(),
            ),
            const SizedBox(height: 16.0),
            ElevatedButton(
              onPressed: _isLoading ? null : _summarizeVideo,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 12.0),
              ),
              child: _isLoading
                  ? const CircularProgressIndicator(color: Colors.white)
                  : const Text(
                'Get Summary',
                style: TextStyle(fontSize: 18.0),
              ),
            ),
            const SizedBox(height: 24.0),
            Expanded(
              child: Card(
                elevation: 4.0,
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(16.0),
                  child: Text(
                    _summary,
                    style: const TextStyle(fontSize: 16.0, height: 1.5),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}